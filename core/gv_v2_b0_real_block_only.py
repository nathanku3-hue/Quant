"""GV-V2-B0A local-source abstention — one MU research-card package, fail-closed.

Classification (honest product identity):

  GV-V2-B0A-LOCAL-SOURCE-ABSTENTION

Vertical (bounded local preflight; not real external admission):

  out-of-band local evaluation authorization
  → exact immutable repository source bytes
  → package-manifest binding validation
  → admission checks (licence, PIT, identity, schema, completeness,
    contradiction, purpose, forbidden use)
  → exact admission BLOCK only (no positive ADMITTED path)
  → one MU G_supply research HOLD
  → DecisionEnvelope → PortfolioBook → Fs0Certification
  → visible operator decision (paper NO_POSITION)

A certified local source-authority abstention is a successful functional
result when real point-in-time authority is inadequate.

No generic provider platform. No DataAdmissionCertificate in B0A.
No automatic ADVANCE_TO_FULL_RESEARCH. No synthetic-as-real evidence.
No score uplift. No credentials in authorization artifacts.
"""

from __future__ import annotations

import json
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

CASE_ID = "V2_B0_MU_G_SUPPLY_BLOCK_ONLY_1"
SUBJECT = "MU"
MODULE = "G_supply"
DECISION_ID = "DECISION_V2_B0_MU_G_SUPPLY_1"
SLICE_CLASSIFICATION = "GV-V2-B0A-LOCAL-SOURCE-ABSTENTION"
RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
RESEARCH_ACTION_ADVANCE = "ADVANCE_TO_FULL_RESEARCH"
RESEARCH_ACTION_REJECT = "REJECT_THESIS"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"

ACCESS_AUTH_SCHEMA = "gv_v2_b0_data_access_authorization_v1"
SOURCE_MANIFEST_SCHEMA = "gv_v2_b0_source_manifest_v1"
ADMISSION_SCHEMA = "gv_v2_b0_admission_result_v1"
RESEARCH_SCHEMA = "gv_v2_b0_research_decision_v1"
RESULT_SCHEMA = "gv_v2_b0_result_v1"

ACCESS_AUTH_DOMAIN = "GV-V2-B0:DATA_ACCESS_AUTH:V1"
SOURCE_MANIFEST_DOMAIN = "GV-V2-B0:SOURCE_MANIFEST:V1"
ADMISSION_DOMAIN = "GV-V2-B0:ADMISSION:V1"
RESEARCH_DOMAIN = "GV-V2-B0:RESEARCH_DECISION:V1"
RESULT_DOMAIN = "GV-V2-B0:RESULT:V1"

RATIONALE_REF_PREFIX = "V2B0:ADM:"

BLOCK_MISSING_PIT = "MISSING_POINT_IN_TIME_AUTHORITY"
BLOCK_DATA_ABSTENTION = "DATA_ABSTENTION"
BLOCK_LICENCE = "LICENCE_NOT_AUTHORIZED"
BLOCK_PURPOSE = "PURPOSE_INCOMPATIBLE"
BLOCK_CONTRADICTION = "CONTRADICTORY_INDISPENSABLE_EVIDENCE"
BLOCK_COMPLETENESS = "INCOMPLETE_INDISPENSABLE_EVIDENCE"
BLOCK_MANIFEST_BINDING = "SOURCE_PACKAGE_MANIFEST_BINDING_INVALID"
BLOCK_POSITIVE_ADMISSION = "V2B0_POSITIVE_ADMISSION_NOT_AUTHORIZED"

AUTH_PROVENANCE_LOCAL = "OUT_OF_BAND_OWNER_APPROVAL_FOR_LOCAL_EVALUATION_ONLY"
PURPOSE_LOCAL_ABSTENTION = "GV_V2_B0A_LOCAL_SOURCE_ABSTENTION_MU_G_SUPPLY"

DEFAULT_CASE_DIR = ROOT / "data" / "gv_v2_b0" / "mu_g_supply_b0"
DEFAULT_ACCESS_AUTH_PATH = DEFAULT_CASE_DIR / "access_authorization.json"
DEFAULT_SOURCE_MANIFEST_PATH = DEFAULT_CASE_DIR / "source_manifest.json"
DEFAULT_ADMISSION_PATH = DEFAULT_CASE_DIR / "admission_result.json"
DEFAULT_RESEARCH_PATH = DEFAULT_CASE_DIR / "research_decision.json"
DEFAULT_RESULT_PATH = DEFAULT_CASE_DIR / "result.json"
DEFAULT_DECISION_PACKET_PATH = DEFAULT_CASE_DIR / "decision_packet.md"

# One local package only: existing MU research card (not real PIT supply evidence).
MU_CARD_REL = "data/candidate_cards/MU_supercycle_candidate_card_v0.json"
MU_CARD_MANIFEST_REL = "data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json"
# Repository blob identity (LF-normalized; see .gitattributes data/candidate_cards/**).
EXPECTED_MU_CARD_SHA256 = (
    "f87e7908854791c327b3a04eb46b873fb995283a4b8015c1bca7bd7066f53f2d"
)

CLAIM_BOUNDARY = (
    "V2-B0A local research-card admission preflight / certified source-authority "
    "abstention for one MU G_supply package. Not a real external source admission. "
    "No established mispricing, alpha, investability, tradability, trade "
    "recommendation, score uplift, or general decision improvement claim. "
    "A certified local-source abstention is a valid functional result. "
    "Research HOLD_FOR_EVIDENCE maps only to paper NO_POSITION. "
    "Positive ADMITTED / ADVANCE_TO_FULL_RESEARCH is not authorized in B0A."
)


class GvV2B0Error(RuntimeError):
    """Fail-closed V2-B0A local-source abstention error."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _require_file(path: Path, code: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise GvV2B0Error(code)
    return path


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(_plain(payload), sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical_json_bytes(payload)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)
    if path.read_bytes() != raw:
        raise GvV2B0Error(f"V2B0_WRITE_VERIFY_FAILED:{path.name}")
    return sha256(raw).hexdigest()


def _primary_block_reason(blocks: list[str]) -> str:
    priority = (
        BLOCK_POSITIVE_ADMISSION,
        BLOCK_MISSING_PIT,
        BLOCK_MANIFEST_BINDING,
        BLOCK_LICENCE,
        BLOCK_PURPOSE,
        BLOCK_COMPLETENESS,
        BLOCK_CONTRADICTION,
        BLOCK_DATA_ABSTENTION,
    )
    present = set(blocks)
    for code in priority:
        if code in present:
            return code
    return BLOCK_DATA_ABSTENTION


def build_data_access_authorization(
    *,
    root: Path | None = None,
    authorized_by: str = "OWNER_V2_B0_GATE",
    authorized_at: str = "2026-07-22T00:00:00.000000Z",
) -> dict[str, Any]:
    """Out-of-band local-evaluation scope grant for one repository MU package.

    Does **not** authorize real provider network reads, WRDS probes, or
    investable/promotional uses. Contains no credentials. Not a verified
    source receipt; ``retrieval_or_receipt_time`` is unknown.
    """

    base = Path(root) if root is not None else ROOT
    card = _require_file(base / MU_CARD_REL, "V2B0_SOURCE_PACKAGE_MISSING")
    card_sha = _sha256_file(card)
    if card_sha != EXPECTED_MU_CARD_SHA256:
        raise GvV2B0Error("V2B0_SOURCE_PACKAGE_HASH_MISMATCH")
    body = {
        "schema_version": ACCESS_AUTH_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "provider_identity": "LOCAL_REPOSITORY_ARTIFACT",
        "source_identity": MU_CARD_REL,
        "source_type": "manual_research_candidate_card",
        "licence_owner": "repository_operator",
        "permitted_use": [
            "v2_b0_admission_evaluation_only",
            "fail_closed_point_in_time_gate",
            "local_source_abstention_preflight",
        ],
        "forbidden_use": [
            "real_provider_network_read",
            "wrds_probe",
            "alpha_search",
            "ranking",
            "broker_order",
            "live_capital",
            "score_uplift",
            "synthetic_as_real_evidence",
            "positive_admission_publication",
            "automatic_research_advancement",
        ],
        "purpose": PURPOSE_LOCAL_ABSTENTION,
        "credentials_boundary": "none_present_none_authorized",
        # Not proven source receipt metadata — unknown for local preflight.
        "retrieval_or_receipt_time": None,
        "authorization_recorded_at": authorized_at,
        "authorization_provenance": AUTH_PROVENANCE_LOCAL,
        "coverage": {
            "entity": "MU",
            "scope": "single_local_package",
            "real_provider_read_authorized": False,
        },
        "restrictions": [
            "Package is research-card identity only; not official filing or physical supply evidence.",
            "Authorization is out-of-band local evaluation only; not detached source-specific authority.",
            "Authorization does not grant candidate admission.",
            "No current snapshot may substitute for point-in-time authority.",
            "Positive ADMITTED path is not authorized in B0A.",
        ],
        "accountable_authorizer": authorized_by,
        "repository_artifact_path": MU_CARD_REL,
        "repository_artifact_sha256": card_sha,
        "authorized_actions": [
            "hash_local_bytes",
            "run_admission_checks",
            "emit_admission_block_only",
            "route_hold_no_position",
        ],
        "expiration_or_revocation": "round_scoped_gate_only",
        "alpha_claim": False,
        "slice_classification": SLICE_CLASSIFICATION,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["authorization_hash"] = domain_hash(ACCESS_AUTH_DOMAIN, body)
    return body


def build_source_manifest(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve exact package bytes/hashes and required timing/identity fields."""

    base = Path(root) if root is not None else ROOT
    auth = (
        _plain(access_authorization)
        if access_authorization is not None
        else build_data_access_authorization(root=base)
    )
    paths = [MU_CARD_REL, MU_CARD_MANIFEST_REL]
    files: list[dict[str, Any]] = []
    for rel in paths:
        path = _require_file(base / rel, f"V2B0_SOURCE_FILE_MISSING:{rel}")
        raw = path.read_bytes()
        files.append(
            {
                "path": rel,
                "byte_length": len(raw),
                "sha256": sha256(raw).hexdigest(),
            }
        )
    # Attempted real PIT fields — absent for this package (fail-closed).
    body = {
        "schema_version": SOURCE_MANIFEST_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "access_authorization_hash": auth["authorization_hash"],
        "files": files,
        "publication_time": None,
        "known_at": None,
        "effective_period": None,
        "revision_or_vintage_state": "research_card_no_filing_vintage",
        "units": None,
        "entity_identity": {
            "ticker": "MU",
            "company_name": "Micron Technology, Inc.",
            "identity_source": MU_CARD_REL,
        },
        "upstream_duplication": "single_local_research_card",
        "point_in_time_available": False,
        "real_physical_supply_bytes_present": False,
        "official_company_filing_bytes_present": False,
        "slice_classification": SLICE_CLASSIFICATION,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["source_manifest_hash"] = domain_hash(SOURCE_MANIFEST_DOMAIN, body)
    return body


def _validate_package_manifest_binding(
    *,
    base: Path,
) -> tuple[bool, str]:
    """Validate historical package manifest binds the actual card URI/hash.

    Historical bytes are preserved even when the declared hash is wrong;
    admission must surface the contradiction rather than rewrite the package.
    """

    card_path = base / MU_CARD_REL
    pkg_manifest_path = base / MU_CARD_MANIFEST_REL
    if not card_path.is_file() or not pkg_manifest_path.is_file():
        return False, "package_card_or_manifest_missing"
    try:
        pkg_manifest = json.loads(pkg_manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"package_manifest_unreadable:{exc}"
    if not isinstance(pkg_manifest, dict):
        return False, "package_manifest_not_object"
    declared_uri = pkg_manifest.get("artifact_uri")
    declared_sha = pkg_manifest.get("artifact_sha256")
    actual_sha = _sha256_file(card_path)
    notes: list[str] = []
    if declared_uri != MU_CARD_REL:
        notes.append(f"uri_mismatch:declared={declared_uri!r}")
    if not isinstance(declared_sha, str) or len(declared_sha) != 64:
        notes.append("declared_sha_invalid")
    elif declared_sha != actual_sha:
        notes.append(
            f"sha_mismatch:declared={declared_sha}:actual={actual_sha}"
        )
    if actual_sha != EXPECTED_MU_CARD_SHA256:
        notes.append("actual_card_not_pinned_blob")
    if notes:
        return False, "; ".join(notes)
    return True, "package_manifest_binds_actual_card"


def run_admission_checks(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed admission: emit exact BLOCK only. Never publish ADMITTED."""

    base = Path(root) if root is not None else ROOT
    auth = (
        _plain(access_authorization)
        if access_authorization is not None
        else build_data_access_authorization(root=base)
    )
    manifest = (
        _plain(source_manifest)
        if source_manifest is not None
        else build_source_manifest(root=base, access_authorization=auth)
    )
    if manifest.get("access_authorization_hash") != auth.get("authorization_hash"):
        raise GvV2B0Error("V2B0_AUTH_MANIFEST_BINDING_INVALID")

    checks: dict[str, dict[str, Any]] = {}
    blocks: list[str] = []

    # 1) Licence / permitted use
    permitted = set(auth.get("permitted_use") or [])
    forbidden = set(auth.get("forbidden_use") or [])
    licence_ok = (
        "v2_b0_admission_evaluation_only" in permitted
        and "real_provider_network_read" in forbidden
        and "synthetic_as_real_evidence" in forbidden
    )
    checks["licence_and_permitted_use"] = {
        "pass": licence_ok,
        "detail": "Access auth is local evaluation-only; investable/real-provider uses forbidden.",
    }
    if not licence_ok:
        blocks.append(BLOCK_LICENCE)

    # 2) Point-in-time availability
    pit_ok = (
        manifest.get("point_in_time_available") is True
        and manifest.get("known_at") is not None
        and manifest.get("publication_time") is not None
        and manifest.get("effective_period") is not None
    )
    checks["point_in_time_availability"] = {
        "pass": pit_ok,
        "detail": "No known_at/publication_time/effective_period for physical supply facts.",
    }
    if not pit_ok:
        blocks.append(BLOCK_MISSING_PIT)

    # 3) Immutable byte identity (tracked source_manifest files vs disk)
    identity_ok = True
    identity_notes: list[str] = []
    for item in manifest.get("files") or []:
        rel = str(item["path"])
        path = base / rel
        if not path.is_file():
            identity_ok = False
            identity_notes.append(f"missing:{rel}")
            continue
        digest = _sha256_file(path)
        if digest != item.get("sha256"):
            identity_ok = False
            identity_notes.append(f"hash_mismatch:{rel}")
        if rel == MU_CARD_REL and digest != EXPECTED_MU_CARD_SHA256:
            identity_ok = False
            identity_notes.append("mu_card_expected_hash_mismatch")
    checks["immutable_byte_identity"] = {
        "pass": identity_ok,
        "detail": "; ".join(identity_notes) if identity_notes else "exact hashes verified",
    }
    if not identity_ok:
        blocks.append(BLOCK_DATA_ABSTENTION)

    # 3b) Historical package-manifest binding (URI + declared artifact_sha256)
    binding_ok, binding_detail = _validate_package_manifest_binding(base=base)
    checks["package_manifest_binding"] = {
        "pass": binding_ok,
        "detail": binding_detail,
    }
    if not binding_ok:
        blocks.append(BLOCK_MANIFEST_BINDING)

    # 4) Semantic / schema validity for G_supply real-evidence admission
    card = json.loads((base / MU_CARD_REL).read_text(encoding="utf-8"))
    quality = card.get("source_quality_summary") or {}
    has_real_supply = bool(manifest.get("real_physical_supply_bytes_present"))
    has_filing = bool(manifest.get("official_company_filing_bytes_present"))
    semantic_ok = has_real_supply or has_filing
    checks["semantic_and_schema_validity"] = {
        "pass": semantic_ok,
        "detail": (
            "Research candidate card is schema-valid as research_only identity, "
            "but is not a G_supply real-admission evidence schema."
        ),
    }
    if not semantic_ok:
        blocks.append(BLOCK_COMPLETENESS)

    # 5) Completeness for indispensable G_supply admission
    missing = list(quality.get("missing") or [])
    complete_ok = (
        semantic_ok
        and not missing
        and has_real_supply
        and has_filing
    )
    checks["completeness"] = {
        "pass": complete_ok,
        "detail": f"missing_declared={len(missing)}; real_supply={has_real_supply}; filing={has_filing}",
    }
    if not complete_ok and BLOCK_COMPLETENESS not in blocks:
        blocks.append(BLOCK_COMPLETENESS)

    # 6) Contradictions among indispensable admitted facts
    # No admitted indispensable facts → vacuous pass (not a free pass to ADMITTED).
    checks["contradictions"] = {
        "pass": True,
        "detail": "No admitted indispensable real facts to contradict; contradiction check vacuous.",
    }

    # 7) Purpose compatibility (local abstention preflight)
    purpose = str(auth.get("purpose") or "")
    purpose_ok = purpose == PURPOSE_LOCAL_ABSTENTION
    checks["purpose_compatibility"] = {
        "pass": purpose_ok,
        "detail": (
            "Gate purpose is local research-card admission preflight / "
            "certified source-authority abstention; not real external admission."
        ),
    }
    if not purpose_ok:
        blocks.append(BLOCK_PURPOSE)

    # 8) Forbidden-use enforcement (computed result is authoritative)
    forbidden_ok = "synthetic_as_real_evidence" in forbidden and not semantic_ok
    checks["forbidden_use_enforcement"] = {
        "pass": forbidden_ok,
        "detail": (
            "Research card not promoted to real evidence; forbidden synthetic-as-real held."
            if forbidden_ok
            else "Forbidden-use enforcement failed (synthetic-as-real risk or missing ban)."
        ),
    }
    if not forbidden_ok:
        blocks.append(BLOCK_DATA_ABSTENTION)

    # B0A never publishes positive admission. If checks would otherwise clear,
    # reject explicitly rather than emit ADMITTED / certificate / advancement.
    if not blocks and all(c["pass"] for c in checks.values()):
        blocks.append(BLOCK_POSITIVE_ADMISSION)
        checks["positive_admission_gate"] = {
            "pass": False,
            "detail": "B0A rejects positive ADMITTED publication; use B0B for official-source intake.",
        }
    else:
        checks["positive_admission_gate"] = {
            "pass": True,
            "detail": "No ADMITTED path taken; block-only local abstention retained.",
        }

    primary_block = _primary_block_reason(blocks)
    result_body: dict[str, Any] = {
        "schema_version": ADMISSION_SCHEMA,
        "case_id": CASE_ID,
        "status": "BLOCKED",
        "primary_block_reason": primary_block,
        "block_reasons": sorted(set(blocks)),
        "checks": checks,
        "access_authorization_hash": auth["authorization_hash"],
        "source_manifest_hash": manifest["source_manifest_hash"],
        "admission_certificate": None,
        "slice_classification": SLICE_CLASSIFICATION,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    result_body["admission_hash"] = domain_hash(ADMISSION_DOMAIN, result_body)
    return result_body


def build_g_supply_research_decision(
    admission: Mapping[str, Any],
) -> dict[str, Any]:
    """One MU G_supply evaluation from admission result.

    B0A separation: ADMITTED ≠ research advancement. Positive admission is
    not authorized in this slice.
    """

    admission = _plain(admission)
    if admission.get("status") == "ADMITTED":
        raise GvV2B0Error(BLOCK_POSITIVE_ADMISSION)
    if admission.get("status") != "BLOCKED":
        raise GvV2B0Error("V2B0_ADMISSION_STATUS_INVALID")

    research_action = RESEARCH_ACTION_HOLD
    primary = admission.get("primary_block_reason") or BLOCK_DATA_ABSTENTION
    rationale = (
        f"Admission blocked ({primary}). Local research-card package lacks real "
        "point-in-time physical-supply or official filing authority for MU G_supply. "
        "HOLD_FOR_EVIDENCE is the correct research-triage abstention; "
        "REJECT_THESIS would overclaim thesis death from data absence. "
        "Positive ADMITTED / ADVANCE_TO_FULL_RESEARCH is not authorized in B0A."
    )
    body = {
        "schema_version": RESEARCH_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "research_action": research_action,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "decision_id": DECISION_ID,
        "admission_hash": admission["admission_hash"],
        "admission_status": admission.get("status"),
        "primary_block_reason": admission.get("primary_block_reason"),
        "rationale": rationale,
        "slice_classification": SLICE_CLASSIFICATION,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    research_hash = domain_hash(RESEARCH_DOMAIN, body)
    body["research_decision_hash"] = research_hash
    body["rationale_ref"] = f"{RATIONALE_REF_PREFIX}{admission['admission_hash']}"
    if len(body["rationale_ref"]) > 128:
        raise GvV2B0Error("V2B0_RATIONALE_REF_TOO_LONG")
    return body


def v2b0_rationale_ref(admission_hash: str) -> str:
    digest = str(admission_hash)
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise GvV2B0Error("V2B0_ADMISSION_HASH_INVALID")
    return f"{RATIONALE_REF_PREFIX}{digest}"


def build_v2b0_decision(
    fixture_hash: str,
    fixture_id: str,
    *,
    rationale_ref: str,
) -> DecisionEnvelope:
    if not rationale_ref.startswith(RATIONALE_REF_PREFIX):
        raise GvV2B0Error("V2B0_RATIONALE_REF_PREFIX_INVALID")
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id=DECISION_ID,
        action=PORTFOLIO_ACTION_NO_POSITION,
        requested_quantity=None,
        rationale_ref=rationale_ref,
    )


def build_v2b0_book(*, research: Mapping[str, Any]) -> OpenBookBuild:
    rationale_ref = str(research["rationale_ref"])

    def decision_builder(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
        return build_v2b0_decision(
            fixture_hash,
            fixture_id,
            rationale_ref=rationale_ref,
        )

    return _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )


def build_v2b0_certified_result(
    research: Mapping[str, Any],
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    certified = build_certified_result_from_book(
        build_v2b0_book(research=research),
        verifier_runner,
    )
    decision = certified.get("decision")
    if not isinstance(decision, Mapping):
        raise GvV2B0Error("V2B0_DECISION_REQUIRED")
    if decision.get("decision_id") != DECISION_ID:
        raise GvV2B0Error("V2B0_DECISION_ID_REQUIRED")
    if decision.get("action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvV2B0Error("V2B0_PORTFOLIO_ACTION_REQUIRED")
    if decision.get("rationale_ref") != research.get("rationale_ref"):
        raise GvV2B0Error("V2B0_RATIONALE_BINDING_INVALID")
    if certified.get("certification", {}).get("certification_status") != "CERTIFIED":
        raise GvV2B0Error("V2B0_CERTIFIED_STATUS_REQUIRED")
    return certified


def build_decision_packet_markdown(
    *,
    access_authorization: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> str:
    cert = certified.get("certification") or {}
    decision = certified.get("decision") or {}
    lines = [
        "# GV-V2-B0A Decision Packet — MU G_supply Local Source Abstention",
        "",
        f"- slice_classification: `{SLICE_CLASSIFICATION}`",
        f"- case_id: `{CASE_ID}`",
        f"- subject/module: `{SUBJECT}` / `{MODULE}`",
        f"- access_authorization_hash: `{access_authorization['authorization_hash']}`",
        f"- authorization_provenance: `{access_authorization.get('authorization_provenance')}`",
        f"- retrieval_or_receipt_time: `{access_authorization.get('retrieval_or_receipt_time')}`",
        f"- source_manifest_hash: `{source_manifest['source_manifest_hash']}`",
        f"- admission_hash: `{admission['admission_hash']}`",
        f"- admission_status: `{admission['status']}`",
        f"- primary_block_reason: `{admission.get('primary_block_reason')}`",
        f"- research_action: `{research['research_action']}`",
        f"- portfolio_action: `{research['portfolio_action']}`",
        f"- decision_id: `{decision.get('decision_id')}`",
        f"- rationale_ref: `{decision.get('rationale_ref')}`",
        f"- certification_status: `{cert.get('certification_status')}`",
        f"- shipped_product_score: `39` (frozen; no uplift)",
        f"- functional_stage: `CERTIFIED_SINGLE_DECISION_OPERABLE`",
        f"- observed_comparison_count: `0` (B0A is local abstention, not G08 observation)",
        "",
        "## Source package",
        f"- path: `{MU_CARD_REL}`",
        f"- sha256: `{EXPECTED_MU_CARD_SHA256}`",
        "- class: local research candidate card (not official filing / not physical supply)",
        "- note: package manifest may declare a non-binding historical artifact_sha256; "
        "admission surfaces SOURCE_PACKAGE_MANIFEST_BINDING_INVALID when so.",
        "",
        "## Admission checks (fail-closed; block-only)",
    ]
    for name, check in sorted((admission.get("checks") or {}).items()):
        lines.append(
            f"- `{name}`: `{'PASS' if check.get('pass') else 'FAIL'}` — {check.get('detail')}"
        )
    lines.extend(
        [
            "",
            "## Research rationale",
            str(research.get("rationale")),
            "",
            "## Claim boundary",
            CLAIM_BOUNDARY,
            "",
        ]
    )
    return "\n".join(lines)


def build_result_document(
    *,
    access_authorization: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> dict[str, Any]:
    body = {
        "schema_version": RESULT_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "slice_classification": SLICE_CLASSIFICATION,
        "access_authorization_hash": access_authorization["authorization_hash"],
        "source_manifest_hash": source_manifest["source_manifest_hash"],
        "admission_hash": admission["admission_hash"],
        "admission_status": admission["status"],
        "primary_block_reason": admission.get("primary_block_reason"),
        "block_reasons": list(admission.get("block_reasons") or []),
        "research_decision_hash": research["research_decision_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "decision_id": certified["decision"]["decision_id"],
        "rationale_ref": certified["decision"]["rationale_ref"],
        "certification_status": certified["certification"]["certification_status"],
        "certified_decision_result_hash": certified.get("certified_decision_result_hash"),
        "shipped_product_score": 39,
        "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
        "observed_comparison_count": 0,
        "local_source_abstention_verticals": 1,
        "real_external_source_packages_processed": 0,
        "data_admission_certificates_earned": 0,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["result_hash"] = domain_hash(RESULT_DOMAIN, body)
    return body


def run_v2_b0_real_block_only(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    publish: bool = True,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Execute the full V2-B0A local-abstention vertical once; bank artifacts."""

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else (base / "data" / "gv_v2_b0" / "mu_g_supply_b0")
    out_dir.mkdir(parents=True, exist_ok=True)

    auth = build_data_access_authorization(root=base)
    manifest = build_source_manifest(root=base, access_authorization=auth)
    admission = run_admission_checks(
        root=base, access_authorization=auth, source_manifest=manifest
    )
    if admission.get("status") == "ADMITTED":
        raise GvV2B0Error(BLOCK_POSITIVE_ADMISSION)
    research = build_g_supply_research_decision(admission)
    if research.get("research_action") == RESEARCH_ACTION_ADVANCE:
        raise GvV2B0Error(BLOCK_POSITIVE_ADMISSION)
    certified = build_v2b0_certified_result(research, verifier_runner)
    result = build_result_document(
        access_authorization=auth,
        source_manifest=manifest,
        admission=admission,
        research=research,
        certified=certified,
    )
    packet_md = build_decision_packet_markdown(
        access_authorization=auth,
        source_manifest=manifest,
        admission=admission,
        research=research,
        certified=certified,
    )

    _atomic_write_json(out_dir / "access_authorization.json", auth)
    _atomic_write_json(out_dir / "source_manifest.json", manifest)
    _atomic_write_json(out_dir / "admission_result.json", admission)
    _atomic_write_json(out_dir / "research_decision.json", research)
    _atomic_write_json(out_dir / "result.json", result)
    packet_path = out_dir / "decision_packet.md"
    packet_path.write_text(packet_md, encoding="utf-8", newline="\n")

    publication: CurrentDecisionPublicationResult | None = None
    if publish:
        publication = publish_current_decision(
            certified, target=current_target, lock_path=current_lock
        )

    return {
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "admission_status": admission["status"],
        "primary_block_reason": admission.get("primary_block_reason"),
        "block_reasons": list(admission.get("block_reasons") or []),
        "admission_hash": admission["admission_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "decision_id": DECISION_ID,
        "rationale_ref": research["rationale_ref"],
        "certification_status": certified["certification"]["certification_status"],
        "result_hash": result["result_hash"],
        "case_dir": str(out_dir),
        "published": publication is not None,
        "publication_status": getattr(publication, "status", None),
        "shipped_product_score": 39,
        "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
        "observed_comparison_count": 0,
    }


__all__ = [
    "ADMISSION_SCHEMA",
    "AUTH_PROVENANCE_LOCAL",
    "BLOCK_COMPLETENESS",
    "BLOCK_CONTRADICTION",
    "BLOCK_DATA_ABSTENTION",
    "BLOCK_LICENCE",
    "BLOCK_MANIFEST_BINDING",
    "BLOCK_MISSING_PIT",
    "BLOCK_POSITIVE_ADMISSION",
    "BLOCK_PURPOSE",
    "CASE_ID",
    "CLAIM_BOUNDARY",
    "DECISION_ID",
    "DEFAULT_CASE_DIR",
    "EXPECTED_MU_CARD_SHA256",
    "MODULE",
    "MU_CARD_REL",
    "MU_CARD_MANIFEST_REL",
    "PORTFOLIO_ACTION_NO_POSITION",
    "PURPOSE_LOCAL_ABSTENTION",
    "RATIONALE_REF_PREFIX",
    "RESEARCH_ACTION_ADVANCE",
    "RESEARCH_ACTION_HOLD",
    "SLICE_CLASSIFICATION",
    "SUBJECT",
    "GvV2B0Error",
    "build_data_access_authorization",
    "build_g_supply_research_decision",
    "build_source_manifest",
    "build_v2b0_book",
    "build_v2b0_certified_result",
    "build_v2b0_decision",
    "run_admission_checks",
    "run_v2_b0_real_block_only",
    "v2b0_rationale_ref",
]
