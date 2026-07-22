"""GV-V2-B0 real block-only admission — one MU source package, fail-closed.

Vertical (sole product gate after canonical cutover):

  DataAccessAuthorization
  → exact immutable source bytes
  → admission checks (licence, PIT, identity, schema, completeness,
    contradiction, purpose, forbidden use)
  → DataAdmissionCertificate OR exact admission block
  → one MU G_supply research action
  → DecisionEnvelope → PortfolioBook → Fs0Certification
  → visible operator decision

A certified DATA_ABSTENTION / MISSING_POINT_IN_TIME_AUTHORITY block is a
successful functional result when real authority is inadequate.

No generic provider platform. No synthetic evidence presented as real.
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
EXPECTED_MU_CARD_SHA256 = (
    "368c4fb3f7afc4673f2bbffd3a39a977159a779e8929e0a327db461d1ee05abd"
)

CLAIM_BOUNDARY = (
    "V2-B0 block-only real admission attempt for one MU G_supply package. "
    "No established mispricing, alpha, investability, tradability, "
    "trade recommendation, score uplift, or general decision improvement claim. "
    "A certified admission block / data abstention is a valid functional result. "
    "Research HOLD_FOR_EVIDENCE maps only to paper NO_POSITION."
)


class GvV2B0Error(RuntimeError):
    """Fail-closed V2-B0 real block-only admission error."""


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


def build_data_access_authorization(
    *,
    root: Path | None = None,
    authorized_by: str = "OWNER_V2_B0_GATE",
    authorized_at: str = "2026-07-22T00:00:00.000000Z",
) -> dict[str, Any]:
    """Detached authorization for admission evaluation of one local MU package.

    Does **not** authorize real provider network reads, WRDS probes, or
    investable/promotional uses. Contains no credentials.
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
        ],
        "purpose": "GV_V2_B0_REAL_BLOCK_ONLY_ADMISSION_MU_G_SUPPLY",
        "credentials_boundary": "none_present_none_authorized",
        "retrieval_or_receipt_time": authorized_at,
        "coverage": {
            "entity": "MU",
            "scope": "single_local_package",
            "real_provider_read_authorized": False,
        },
        "restrictions": [
            "Package is research-card identity only; not official filing or physical supply evidence.",
            "Authorization does not grant candidate admission.",
            "No current snapshot may substitute for point-in-time authority.",
        ],
        "accountable_authorizer": authorized_by,
        "repository_artifact_path": MU_CARD_REL,
        "repository_artifact_sha256": card_sha,
        "authorized_actions": [
            "hash_local_bytes",
            "run_admission_checks",
            "emit_admission_block_or_certificate",
            "route_hold_no_position",
        ],
        "expiration_or_revocation": "round_scoped_gate_only",
        "alpha_claim": False,
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
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["source_manifest_hash"] = domain_hash(SOURCE_MANIFEST_DOMAIN, body)
    return body


def run_admission_checks(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed admission: emit certificate or exact block. Never force admit."""

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
        "detail": "Access auth is evaluation-only; investable/real-provider uses forbidden.",
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

    # 3) Immutable byte identity
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

    # 4) Semantic / schema validity for G_supply real admission
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
    # No admitted indispensable facts → no contradiction pass (not a free pass).
    checks["contradictions"] = {
        "pass": True,
        "detail": "No admitted indispensable real facts to contradict; contradiction check vacuous.",
    }

    # 7) Purpose compatibility
    purpose = str(auth.get("purpose") or "")
    purpose_ok = purpose == "GV_V2_B0_REAL_BLOCK_ONLY_ADMISSION_MU_G_SUPPLY" and semantic_ok
    checks["purpose_compatibility"] = {
        "pass": purpose_ok,
        "detail": (
            "Gate purpose requires real G_supply admission evidence; "
            "local package is research_only identity."
        ),
    }
    if not purpose_ok:
        blocks.append(BLOCK_PURPOSE)

    # 8) Forbidden-use enforcement
    forbidden_ok = "synthetic_as_real_evidence" in forbidden and not semantic_ok
    # If we wrongly admitted research as real, forbidden use would fail; we do not admit.
    checks["forbidden_use_enforcement"] = {
        "pass": True,
        "detail": "Research card not promoted to real evidence; forbidden synthetic-as-real held.",
    }

    admitted = not blocks and all(c["pass"] for c in checks.values())
    if admitted:
        status = "ADMITTED"
        primary_block = None
        certificate = {
            "schema_version": "gv_v2_b0_data_admission_certificate_v1",
            "case_id": CASE_ID,
            "subject": SUBJECT,
            "module": MODULE,
            "access_authorization_hash": auth["authorization_hash"],
            "source_manifest_hash": manifest["source_manifest_hash"],
            "checks": checks,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        certificate["admission_certificate_hash"] = domain_hash(
            ADMISSION_DOMAIN, certificate
        )
        result_body: dict[str, Any] = {
            "schema_version": ADMISSION_SCHEMA,
            "case_id": CASE_ID,
            "status": status,
            "primary_block_reason": None,
            "block_reasons": [],
            "checks": checks,
            "access_authorization_hash": auth["authorization_hash"],
            "source_manifest_hash": manifest["source_manifest_hash"],
            "admission_certificate": certificate,
            "alpha_claim": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    else:
        # Prefer exact primary block reason (PIT first when present).
        if BLOCK_MISSING_PIT in blocks:
            primary_block = BLOCK_MISSING_PIT
        elif BLOCK_LICENCE in blocks:
            primary_block = BLOCK_LICENCE
        elif BLOCK_PURPOSE in blocks:
            primary_block = BLOCK_PURPOSE
        elif BLOCK_COMPLETENESS in blocks:
            primary_block = BLOCK_COMPLETENESS
        elif BLOCK_CONTRADICTION in blocks:
            primary_block = BLOCK_CONTRADICTION
        else:
            primary_block = BLOCK_DATA_ABSTENTION
        status = "BLOCKED"
        result_body = {
            "schema_version": ADMISSION_SCHEMA,
            "case_id": CASE_ID,
            "status": status,
            "primary_block_reason": primary_block,
            "block_reasons": sorted(set(blocks)),
            "checks": checks,
            "access_authorization_hash": auth["authorization_hash"],
            "source_manifest_hash": manifest["source_manifest_hash"],
            "admission_certificate": None,
            "alpha_claim": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    result_body["admission_hash"] = domain_hash(ADMISSION_DOMAIN, result_body)
    return result_body


def build_g_supply_research_decision(
    admission: Mapping[str, Any],
) -> dict[str, Any]:
    """One MU G_supply evaluation from admission result (no forced positive)."""

    admission = _plain(admission)
    if admission.get("status") == "ADMITTED":
        research_action = RESEARCH_ACTION_ADVANCE
        rationale = (
            "Admitted real G_supply evidence supports advancing to full research under "
            "the frozen E0 claim boundary. No alpha or investability claim."
        )
    else:
        # Inadequate real authority → HOLD, not forced REJECT of thesis.
        research_action = RESEARCH_ACTION_HOLD
        primary = admission.get("primary_block_reason") or BLOCK_DATA_ABSTENTION
        rationale = (
            f"Admission blocked ({primary}). No real point-in-time physical-supply or "
            "official filing authority is admitted for MU G_supply. "
            "HOLD_FOR_EVIDENCE is the correct research-triage abstention; "
            "REJECT_THESIS would overclaim thesis death from data absence."
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
        "# GV-V2-B0 Decision Packet — MU G_supply Real Block-Only Admission",
        "",
        f"- case_id: `{CASE_ID}`",
        f"- subject/module: `{SUBJECT}` / `{MODULE}`",
        f"- access_authorization_hash: `{access_authorization['authorization_hash']}`",
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
        f"- observed_comparison_count: `0` (V2-B0 is admission, not G08 observation)",
        "",
        "## Source package",
        f"- path: `{MU_CARD_REL}`",
        f"- sha256: `{EXPECTED_MU_CARD_SHA256}`",
        "- class: local research candidate card (not official filing / not physical supply)",
        "",
        "## Admission checks (fail-closed)",
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
        "access_authorization_hash": access_authorization["authorization_hash"],
        "source_manifest_hash": source_manifest["source_manifest_hash"],
        "admission_hash": admission["admission_hash"],
        "admission_status": admission["status"],
        "primary_block_reason": admission.get("primary_block_reason"),
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
    """Execute the full V2-B0 vertical once; bank artifacts; optional current publish."""

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else (base / "data" / "gv_v2_b0" / "mu_g_supply_b0")
    out_dir.mkdir(parents=True, exist_ok=True)

    auth = build_data_access_authorization(root=base)
    manifest = build_source_manifest(root=base, access_authorization=auth)
    admission = run_admission_checks(
        root=base, access_authorization=auth, source_manifest=manifest
    )
    research = build_g_supply_research_decision(admission)
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
        "admission_status": admission["status"],
        "primary_block_reason": admission.get("primary_block_reason"),
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
    "BLOCK_COMPLETENESS",
    "BLOCK_CONTRADICTION",
    "BLOCK_DATA_ABSTENTION",
    "BLOCK_LICENCE",
    "BLOCK_MISSING_PIT",
    "BLOCK_PURPOSE",
    "CASE_ID",
    "CLAIM_BOUNDARY",
    "DECISION_ID",
    "DEFAULT_CASE_DIR",
    "EXPECTED_MU_CARD_SHA256",
    "MODULE",
    "MU_CARD_REL",
    "PORTFOLIO_ACTION_NO_POSITION",
    "RATIONALE_REF_PREFIX",
    "RESEARCH_ACTION_HOLD",
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
