"""GV-ALPHA0 source family two — independent NVDA 10-Q custody vertical.

Bank exact authorized independent issuer package *before* multi-source
reconciliation machinery. One vertical:

  pre-read auth → exact three objects → package/admission
  → 3–5 case-specific facts (true byte locators)
  → operator decision capture
  → certified paper NO_POSITION

Not formal comparison. Not auto-ADVANCE. Score stays 39; observed stays 0.
Family one (B0B MU) remains banked and immutable.
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.gv_fs0_book import (
    DecisionEnvelope,
    OpenBookBuild,
    _build_book,
    _build_decision,
    build_no_position_source_fixture,
)
from core.gv_fs0_canonical import (
    CanonicalizationError,
    domain_hash,
    parse_json_text,
)
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

CASE_ID = "V2_ALPHA0_MU_G_SUPPLY_SOURCE_FAMILY_TWO_1"
SUBJECT_CASE = "MU_G_SUPPLY"
ISSUER_TICKER = "NVDA"
MODULE = "G_supply"
DECISION_ID = "DECISION_V2_ALPHA0_SF2_MU_G_SUPPLY_1"
SLICE_CLASSIFICATION = "GV-ALPHA0-SOURCE-FAMILY-TWO"
SOURCE_FAMILY_ID = "SEC:0001045810-26-000052"
FAMILY_ONE_ID = "SEC:0000723125-26-000015"
ACCESSION = "0001045810-26-000052"
CIK = "0001045810"
FORM = "10-Q"

RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"

ACCESS_AUTH_DOMAIN = "GV-ALPHA0:DATA_ACCESS_AUTH:V1"
PACKAGE_MANIFEST_DOMAIN = "GV-ALPHA0:PACKAGE_MANIFEST:V1"
ADMISSION_DOMAIN = "GV-ALPHA0:ADMISSION:V1"
FACT_SET_DOMAIN = "GV-ALPHA0:FACT_SET:V1"
OPERATOR_CAPTURE_DOMAIN = "GV-ALPHA0:OPERATOR_CAPTURE:V1"
RESEARCH_DOMAIN = "GV-ALPHA0:RESEARCH_DECISION:V1"
RESULT_DOMAIN = "GV-ALPHA0:RESULT:V1"
CERTIFICATE_DOMAIN = "GV-ALPHA0:ADMISSION_CERTIFICATE:V1"

CASE_DIR = ROOT / "data" / "gv_v2_alpha0" / "family_two_nvda_0001045810-26-000052"
RAW_DIR = CASE_DIR / "raw"

EXPECTED_AUTH_HASH = (
    "d1daf403a7850e43dddf7f07663d568a82ad3646a9e7334883a29dd49486f206"
)

PACKAGE_OBJECTS: tuple[dict[str, str], ...] = (
    {
        "role": "accession_index",
        "filename": "0001045810-26-000052-index.htm",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/1045810/"
            "000104581026000052/0001045810-26-000052-index.htm"
        ),
        "expected_sha256": (
            "b90ff3d72a50860b3c2775a0fc2d25f5295b337c4f4e20cb299ee98532b3b34f"
        ),
        "expected_byte_length": "11829",
    },
    {
        "role": "complete_submission",
        "filename": "0001045810-26-000052.txt",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/1045810/"
            "000104581026000052/0001045810-26-000052.txt"
        ),
        "expected_sha256": (
            "fd15a270c0b4ebbfcec982749f940b5cf703e2571e10bd74bc484f233cc68b67"
        ),
        "expected_byte_length": "7515560",
    },
    {
        "role": "primary_10q",
        "filename": "nvda-20260426.htm",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/1045810/"
            "000104581026000052/nvda-20260426.htm"
        ),
        "expected_sha256": (
            "1b5de37b973da4a3f1cd31a09aa455c01c519ea7cc409c73de2250ad156f99e4"
        ),
        "expected_byte_length": "1167053",
    },
)

PINNED_RETRIEVED_AT: dict[str, str] = {
    "0001045810-26-000052-index.htm": "2026-07-22T19:26:10.000000Z",
    "0001045810-26-000052.txt": "2026-07-22T19:26:25.000000Z",
    "nvda-20260426.htm": "2026-07-22T19:26:40.000000Z",
}
PACKAGE_RETRIEVED_AT = "2026-07-22T19:26:40.000000Z"
RETRIEVAL_METHOD = "https_get_sec_edgar_user_agent_declared"

# 3–5 case-specific facts for Alpha family-two vertical (true byte needles).
FACT_NEEDLES: tuple[dict[str, str], ...] = (
    {
        "fact_id": "SF2_FACT_MEMORY_PRICES_001",
        "needle": "elevated memory and systems prices",
        "fact_class": "ISSUER_MARKET_OBSERVATION",
        "section_locator": "MD&A / market commentary",
        "window_before": "60",
        "window_after": "40",
    },
    {
        "fact_id": "SF2_FACT_FOUNDRY_CAPACITY_001",
        "needle": "procure sufficient foundry capacity",
        "fact_class": "SUPPLY_CHAIN_RISK_DISCLOSURE",
        "section_locator": "Risk Factors / supply chain",
        "window_before": "40",
        "window_after": "100",
    },
    {
        "fact_id": "SF2_FACT_SCARCE_INPUTS_001",
        "needle": "scarce input materials during a supply-constrained environment",
        "fact_class": "SUPPLY_CHAIN_RISK_DISCLOSURE",
        "section_locator": "Risk Factors / supply chain",
        "window_before": "20",
        "window_after": "60",
    },
    {
        "fact_id": "SF2_FACT_SUPPLY_SHORTFALL_001",
        "needle": "unable to increase production or provide sufficient supply",
        "fact_class": "SUPPLY_CHAIN_RISK_DISCLOSURE",
        "section_locator": "Risk Factors / demand-supply",
        "window_before": "40",
        "window_after": "80",
    },
    {
        "fact_id": "SF2_FACT_NCNR_ORDERS_001",
        "needle": "non-cancellable and non-returnable purchase orders",
        "fact_class": "CONTRACTUAL_COMMITMENT_DISCLOSURE",
        "section_locator": "Risk Factors / purchase commitments",
        "window_before": "40",
        "window_after": "80",
    },
)

CLAIM_BOUNDARY = (
    "GV-ALPHA0 source family two: independent NVDA 10-Q custody for MU G_supply "
    "preparation. Certified paper only. Does not alone corroborate Micron thesis, "
    "establish physical supply, investability, alpha, or score uplift. Formal "
    "comparison deferred after Alpha. Reconciliation machinery is out of this vertical."
)

RATIONALE_REF_PREFIX = "ALPHA0:SF2:FS:"


class GvAlpha0Sf2Error(ValueError):
    """Fail-closed Alpha source-family-two error."""


def _plain(obj: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(obj))


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _require_file(path: Path, code: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise GvAlpha0Sf2Error(code)
    return path


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(_plain(payload), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical_json_bytes(payload)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)
    if path.read_bytes() != raw:
        raise GvAlpha0Sf2Error(f"ALPHA0_SF2_WRITE_VERIFY_FAILED:{path.name}")
    return _sha256_bytes(raw)


def _load_authority_json(path: Path, *, missing_code: str) -> dict[str, Any]:
    path = _require_file(path, missing_code)
    try:
        obj = parse_json_text(path.read_text(encoding="utf-8"))
    except CanonicalizationError as exc:
        detail = str(exc) if str(exc) else "JSON_AUTHORITY_INVALID"
        raise GvAlpha0Sf2Error(
            f"ALPHA0_SF2_JSON_AUTHORITY_INVALID:{path.name}:{detail}"
        ) from exc
    if not isinstance(obj, dict):
        raise GvAlpha0Sf2Error(f"{missing_code}_NOT_OBJECT")
    return obj


def _parse_ts(value: str) -> str:
    text = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", text):
        return text
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{1,6})Z", text)
    if m:
        return f"{m.group(1)}.{m.group(2).ljust(6, '0')}Z"
    m2 = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z", text)
    if m2:
        return f"{m2.group(1)}.000000Z"
    raise GvAlpha0Sf2Error(f"ALPHA0_SF2_TIMESTAMP_INVALID:{text}")


def _assert_auth_before_receipt(auth_at: str, retrieved_at: str) -> None:
    if not (_parse_ts(auth_at) < _parse_ts(retrieved_at)):
        raise GvAlpha0Sf2Error(
            f"ALPHA0_SF2_AUTH_RECEIPT_ORDERING_INVALID:auth={auth_at}:retrieved={retrieved_at}"
        )


def _package_object_identity_set() -> frozenset[tuple[str, str, str]]:
    return frozenset(
        (str(s["role"]), str(s["filename"]), str(s["official_locator"]))
        for s in PACKAGE_OBJECTS
    )


def _assert_authorized_objects_match_package(auth: Mapping[str, Any]) -> None:
    raw = auth.get("authorized_objects")
    if not isinstance(raw, list) or not raw:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTHORIZED_OBJECTS_MISSING")
    auth_set: set[tuple[str, str, str]] = set()
    for item in raw:
        if not isinstance(item, Mapping):
            raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTHORIZED_OBJECTS_MISMATCH")
        try:
            triple = (
                str(item["role"]),
                str(item["filename"]),
                str(item["official_locator"]),
            )
        except KeyError as exc:
            raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTHORIZED_OBJECTS_MISMATCH") from exc
        if triple in auth_set:
            raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTHORIZED_OBJECTS_MISMATCH")
        auth_set.add(triple)
    if frozenset(auth_set) != _package_object_identity_set():
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTHORIZED_OBJECTS_MISMATCH")


def _byte_window_excerpt(
    data: bytes,
    *,
    needle: str,
    window_before: int,
    window_after: int,
    fact_id: str,
) -> tuple[int, int, str]:
    needle_b = needle.encode("utf-8")
    idx = data.find(needle_b)
    if idx < 0:
        raise GvAlpha0Sf2Error(f"ALPHA0_SF2_FACT_NEEDLE_MISSING:{fact_id}")
    start = max(0, idx - int(window_before))
    end = min(len(data), idx + len(needle_b) + int(window_after))
    if start >= end:
        raise GvAlpha0Sf2Error(f"ALPHA0_SF2_FACT_LOCATOR_INVALID:{fact_id}")
    try:
        excerpt = data[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GvAlpha0Sf2Error(
            f"ALPHA0_SF2_FACT_BYTE_WINDOW_NOT_UTF8:{fact_id}"
        ) from exc
    return start, end, excerpt


def _atomic_write_case_bundle(
    out_dir: Path,
    artifacts: Mapping[str, Mapping[str, Any] | str],
    *,
    promote_order: tuple[str, ...],
) -> None:
    """Result-last fail-closed promote (not multi-file rollback atomicity)."""

    if set(artifacts) != set(promote_order):
        raise GvAlpha0Sf2Error("ALPHA0_SF2_CASE_BUNDLE_ORDER_MISMATCH")
    out_dir.mkdir(parents=True, exist_ok=True)
    staging_root = out_dir / ".alpha0_tx"
    staging = staging_root / f"pending_{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        staged: dict[str, bytes] = {}
        for name, payload in artifacts.items():
            if isinstance(payload, str):
                raw = payload.encode("utf-8")
                if not raw.endswith(b"\n"):
                    raw += b"\n"
            else:
                raw = _canonical_json_bytes(payload)
            (staging / name).write_bytes(raw)
            if (staging / name).read_bytes() != raw:
                raise GvAlpha0Sf2Error(f"ALPHA0_SF2_WRITE_VERIFY_FAILED:{name}")
            staged[name] = raw
        for name in promote_order:
            raw = staged[name]
            final = out_dir / name
            tmp = out_dir / f".{name}.promotetmp"
            tmp.write_bytes(raw)
            tmp.replace(final)
            if final.read_bytes() != raw:
                raise GvAlpha0Sf2Error(f"ALPHA0_SF2_WRITE_VERIFY_FAILED:{name}")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        try:
            if staging_root.is_dir() and not any(staging_root.iterdir()):
                staging_root.rmdir()
        except OSError:
            pass


def load_access_authorization(*, root: Path | None = None) -> dict[str, Any]:
    base = Path(root) if root is not None else ROOT
    auth = _load_authority_json(
        base
        / "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/access_authorization.json",
        missing_code="ALPHA0_SF2_ACCESS_AUTHORIZATION_MISSING",
    )
    if auth.get("retrieval_or_receipt_time") is not None:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_MUST_NOT_CONTAIN_RECEIPT_TIME")
    if auth.get("accession") != ACCESSION or auth.get("cik") != CIK:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_IDENTITY_MISMATCH")
    if auth.get("form") != FORM:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_FORM_MISMATCH")
    body = {k: v for k, v in auth.items() if k != "authorization_hash"}
    recomputed = domain_hash(ACCESS_AUTH_DOMAIN, body)
    if auth.get("authorization_hash") != recomputed:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_HASH_MISMATCH")
    if recomputed != EXPECTED_AUTH_HASH:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_HASH_NOT_PINNED")
    _assert_authorized_objects_match_package(auth)
    return auth


def build_package_manifest(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = Path(root) if root is not None else ROOT
    auth = (
        _plain(access_authorization)
        if access_authorization is not None
        else load_access_authorization(root=base)
    )
    _assert_authorized_objects_match_package(auth)
    raw_dir = (
        base / "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw"
    )
    objects: list[dict[str, Any]] = []
    for spec in PACKAGE_OBJECTS:
        filename = spec["filename"]
        path = _require_file(
            raw_dir / filename, f"ALPHA0_SF2_PACKAGE_OBJECT_MISSING:{filename}"
        )
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        if digest != spec["expected_sha256"]:
            raise GvAlpha0Sf2Error(f"ALPHA0_SF2_PACKAGE_HASH_MISMATCH:{filename}")
        if str(len(data)) != spec["expected_byte_length"]:
            raise GvAlpha0Sf2Error(f"ALPHA0_SF2_PACKAGE_LENGTH_MISMATCH:{filename}")
        retrieved_at = PINNED_RETRIEVED_AT[filename]
        _assert_auth_before_receipt(
            str(auth["authorization_recorded_at"]), retrieved_at
        )
        objects.append(
            {
                "role": spec["role"],
                "filename": filename,
                "relative_path": (
                    "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/"
                    f"raw/{filename}"
                ),
                "official_locator": spec["official_locator"],
                "accession": ACCESSION,
                "sha256": digest,
                "byte_length": len(data),
                "response_sha256": digest,
                "response_byte_length": len(data),
                "retrieved_at": retrieved_at,
            }
        )
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_package_manifest_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "independent_source_role": "source_family_two",
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "accession": ACCESSION,
        "cik": CIK,
        "form": FORM,
        "issuer_ticker": ISSUER_TICKER,
        "independent_source_count": 1,
        "access_authorization_hash": auth["authorization_hash"],
        "authorization_recorded_at": auth["authorization_recorded_at"],
        "retrieved_at": PACKAGE_RETRIEVED_AT,
        "retrieval_method": RETRIEVAL_METHOD,
        "source_locator": (
            "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/"
        ),
        "objects": objects,
        "object_roles": [o["role"] for o in objects],
        "custody_note": (
            "Index, complete submission, and primary 10-Q are custody redundancy "
            "for one NVDA accession. Independent of MU family one; not three "
            "corroborators of Micron claims."
        ),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["package_manifest_hash"] = domain_hash(PACKAGE_MANIFEST_DOMAIN, body)
    return body


def run_admission_checks(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
    package_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = Path(root) if root is not None else ROOT
    auth = (
        _plain(access_authorization)
        if access_authorization is not None
        else load_access_authorization(root=base)
    )
    package = (
        _plain(package_manifest)
        if package_manifest is not None
        else build_package_manifest(root=base, access_authorization=auth)
    )
    if package.get("access_authorization_hash") != auth.get("authorization_hash"):
        raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_PACKAGE_BINDING_INVALID")
    if package.get("source_family_id") != SOURCE_FAMILY_ID:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_SOURCE_FAMILY_MISMATCH")
    if package.get("family_one_reference") != FAMILY_ONE_ID:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_FAMILY_ONE_REFERENCE_MISMATCH")
    if int(package.get("independent_source_count") or 0) != 1:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_INDEPENDENT_COUNT_INVALID")

    cert_body = {
        "schema_version": "gv_alpha0_admission_certificate_v1",
        "case_id": CASE_ID,
        "source_family_id": SOURCE_FAMILY_ID,
        "accession": ACCESSION,
        "package_manifest_hash": package["package_manifest_hash"],
        "access_authorization_hash": auth["authorization_hash"],
        "admission_status": "ADMITTED",
        "certificate_scope": "custody_and_identity_only_not_claim_truth",
    }
    cert_body["admission_certificate_hash"] = domain_hash(
        CERTIFICATE_DOMAIN, cert_body
    )

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_admission_result_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "status": "ADMITTED",
        "primary_block_reason": None,
        "block_reasons": [],
        "package_manifest_hash": package["package_manifest_hash"],
        "access_authorization_hash": auth["authorization_hash"],
        "independent_source_count": 1,
        "checks": {
            "authorization_binding": {"status": "PASS"},
            "package_identity": {"status": "PASS"},
            "object_hashes": {"status": "PASS"},
            "family_independence_from_family_one": {"status": "PASS"},
            "contradictions": {"status": "NOT_EVALUATED", "pass": None},
        },
        "admission_certificate": cert_body,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["admission_hash"] = domain_hash(ADMISSION_DOMAIN, body)
    return body


def extract_case_facts(
    *,
    root: Path | None = None,
    admission: Mapping[str, Any] | None = None,
    package_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract 3–5 case-specific facts with true byte locators."""

    base = Path(root) if root is not None else ROOT
    package = (
        _plain(package_manifest)
        if package_manifest is not None
        else build_package_manifest(root=base)
    )
    adm = (
        _plain(admission)
        if admission is not None
        else run_admission_checks(root=base, package_manifest=package)
    )
    if adm.get("status") != "ADMITTED":
        raise GvAlpha0Sf2Error("ALPHA0_SF2_FACTS_REQUIRE_ADMITTED")

    primary_rel = (
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/nvda-20260426.htm"
    )
    primary_path = _require_file(base / primary_rel, "ALPHA0_SF2_PRIMARY_MISSING")
    data = primary_path.read_bytes()
    source_hash = _sha256_bytes(data)
    facts: list[dict[str, Any]] = []
    for spec in FACT_NEEDLES:
        start, end, excerpt = _byte_window_excerpt(
            data,
            needle=spec["needle"],
            window_before=int(spec["window_before"]),
            window_after=int(spec["window_after"]),
            fact_id=spec["fact_id"],
        )
        facts.append(
            {
                "fact_id": spec["fact_id"],
                "source_object_hash": source_hash,
                "document_locator": primary_rel,
                "official_locator": PACKAGE_OBJECTS[2]["official_locator"],
                "section_or_element_locator": spec["section_locator"],
                "byte_start": start,
                "byte_end": end,
                "exact_excerpt": excerpt,
                "exact_excerpt_hash": _sha256_bytes(excerpt.encode("utf-8")),
                "fact_class": spec["fact_class"],
                "source_family_id": SOURCE_FAMILY_ID,
                "independent_source_count_contribution": 1,
                "subject_case_relevance": SUBJECT_CASE,
            }
        )
    if not (3 <= len(facts) <= 5):
        raise GvAlpha0Sf2Error("ALPHA0_SF2_FACT_COUNT_OUT_OF_RANGE")

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_fact_set_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "admission_hash": adm["admission_hash"],
        "package_manifest_hash": package["package_manifest_hash"],
        "fact_count": len(facts),
        "facts": facts,
        "evaluation_notes": [
            "Case-specific facts extracted under true byte locators.",
            "Facts are NVDA issuer disclosures; not Micron corroboration by themselves.",
            "Reconciliation with family one is out of scope for this vertical.",
        ],
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["fact_set_hash"] = domain_hash(FACT_SET_DOMAIN, body)
    return body


def capture_operator_decision(
    *,
    admission: Mapping[str, Any],
    fact_set: Mapping[str, Any],
    operator_id: str = "SYSTEM_CERTIFIED_PAPER_OPERATOR",
    captured_at: str = "2026-07-22T19:30:00.000000Z",
) -> dict[str, Any]:
    """Record operator decision capture for certified paper path."""

    if admission.get("status") != "ADMITTED":
        raise GvAlpha0Sf2Error("ALPHA0_SF2_OPERATOR_REQUIRES_ADMITTED")
    if int(fact_set.get("fact_count") or 0) < 3:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_OPERATOR_REQUIRES_FACTS")
    rationale_ref = f"{RATIONALE_REF_PREFIX}{fact_set['fact_set_hash']}"
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_operator_decision_capture_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "operator_id": operator_id,
        "captured_at": captured_at,
        "selected_action": PORTFOLIO_ACTION_NO_POSITION,
        "research_stance": RESEARCH_ACTION_HOLD,
        "decision_id": DECISION_ID,
        "rationale_ref": rationale_ref,
        "admission_hash": admission["admission_hash"],
        "fact_set_hash": fact_set["fact_set_hash"],
        "source_families_in_scope": [FAMILY_ONE_ID, SOURCE_FAMILY_ID],
        "reconciliation_status": "NOT_RUN",
        "formal_comparison_status": "DEFERRED_AFTER_ALPHA",
        "notes": (
            "Source family two banked with case-specific facts. "
            "Operator selects certified paper NO_POSITION pending reconciliation. "
            "No score uplift; no live capital; no formal comparison."
        ),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["operator_capture_hash"] = domain_hash(OPERATOR_CAPTURE_DOMAIN, body)
    return body


def build_research_decision(
    admission: Mapping[str, Any],
    fact_set: Mapping[str, Any],
    operator_capture: Mapping[str, Any],
) -> dict[str, Any]:
    if operator_capture.get("selected_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_NON_HOLD_NOT_AUTHORIZED")
    if operator_capture.get("research_stance") != RESEARCH_ACTION_HOLD:
        raise GvAlpha0Sf2Error("ALPHA0_SF2_NON_HOLD_NOT_AUTHORIZED")
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_research_decision_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "module": MODULE,
        "research_action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "decision_id": DECISION_ID,
        "rationale_ref": operator_capture["rationale_ref"],
        "admission_hash": admission["admission_hash"],
        "fact_set_hash": fact_set["fact_set_hash"],
        "operator_capture_hash": operator_capture["operator_capture_hash"],
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "independent_source_count": 1,
        "reconciliation_status": "NOT_RUN",
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["research_decision_hash"] = domain_hash(RESEARCH_DOMAIN, body)
    return body


def _build_certified(
    research: Mapping[str, Any],
    *,
    verifier_runner: VerifierRunner,
) -> dict[str, Any]:
    rationale_ref = str(research["rationale_ref"])

    def decision_builder(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
        return _build_decision(
            fixture_hash=fixture_hash,
            fixture_id=fixture_id,
            decision_id=DECISION_ID,
            action=PORTFOLIO_ACTION_NO_POSITION,
            requested_quantity=None,
            rationale_ref=rationale_ref,
        )

    book = _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )
    return build_certified_result_from_book(book, verifier_runner)


def build_result(
    *,
    access_authorization: Mapping[str, Any],
    package_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    fact_set: Mapping[str, Any],
    operator_capture: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> dict[str, Any]:
    cert = admission.get("admission_certificate") or {}
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_result_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "decision_id": DECISION_ID,
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "access_authorization_hash": access_authorization["authorization_hash"],
        "package_manifest_hash": package_manifest["package_manifest_hash"],
        "admission_hash": admission["admission_hash"],
        "admission_status": admission["status"],
        "admission_certificate_hash": cert.get("admission_certificate_hash"),
        "fact_set_hash": fact_set["fact_set_hash"],
        "fact_count": fact_set["fact_count"],
        "operator_capture_hash": operator_capture["operator_capture_hash"],
        "research_decision_hash": research["research_decision_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "rationale_ref": research["rationale_ref"],
        "certified_decision_result_hash": certified.get(
            "certified_decision_result_hash"
        ),
        "certification_status": certified["certification"]["certification_status"],
        "shipped_product_score": 39,
        "observed_comparison_count": 0,
        "real_external_source_packages_processed": 1,
        "data_admission_certificates_earned": 1,
        "independent_source_count": 1,
        "reconciliation_status": "NOT_RUN",
        "formal_comparison_status": "DEFERRED_AFTER_ALPHA",
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["result_hash"] = domain_hash(RESULT_DOMAIN, body)
    return body


def build_decision_packet_markdown(
    *,
    access_authorization: Mapping[str, Any],
    package_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    fact_set: Mapping[str, Any],
    operator_capture: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> str:
    lines = [
        "# GV-ALPHA0 Source Family Two — Decision Packet",
        "",
        f"- case_id: `{CASE_ID}`",
        f"- slice: `{SLICE_CLASSIFICATION}`",
        f"- subject_case: `{SUBJECT_CASE}`",
        f"- source_family_two: `{SOURCE_FAMILY_ID}`",
        f"- family_one_reference: `{FAMILY_ONE_ID}`",
        f"- accession: `{ACCESSION}` issuer=`{ISSUER_TICKER}`",
        f"- authorization_hash: `{access_authorization['authorization_hash']}`",
        f"- package_manifest_hash: `{package_manifest['package_manifest_hash']}`",
        f"- admission_hash: `{admission['admission_hash']}` status=`{admission['status']}`",
        f"- fact_set_hash: `{fact_set['fact_set_hash']}` count=`{fact_set['fact_count']}`",
        f"- operator_capture_hash: `{operator_capture['operator_capture_hash']}`",
        f"- research: `{research['research_action']}` → `{research['portfolio_action']}`",
        f"- decision_id: `{DECISION_ID}`",
        f"- rationale_ref: `{research['rationale_ref']}`",
        f"- certified: `{certified['certification']['certification_status']}`",
        f"- score/observed: `39` / `0`",
        f"- reconciliation: `NOT_RUN` · formal comparison: `DEFERRED_AFTER_ALPHA`",
        "",
        "## Facts",
    ]
    for fact in fact_set["facts"]:
        lines.append(
            f"- `{fact['fact_id']}` bytes=[{fact['byte_start']},{fact['byte_end']}) "
            f"class=`{fact['fact_class']}`"
        )
    lines.extend(
        [
            "",
            "## Operator capture",
            f"- operator_id: `{operator_capture['operator_id']}`",
            f"- selected_action: `{operator_capture['selected_action']}`",
            f"- notes: {operator_capture['notes']}",
            "",
        ]
    )
    return "\n".join(lines)


def run_v2_alpha0_source_family_two(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    publish: bool = False,
    current_target: Path | None = None,
    current_lock: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else CASE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    auth = load_access_authorization(root=base)
    package = build_package_manifest(root=base, access_authorization=auth)
    admission = run_admission_checks(
        root=base, access_authorization=auth, package_manifest=package
    )
    fact_set = extract_case_facts(
        root=base, admission=admission, package_manifest=package
    )
    operator_capture = capture_operator_decision(
        admission=admission, fact_set=fact_set
    )
    research = build_research_decision(admission, fact_set, operator_capture)
    certified = _build_certified(research, verifier_runner=verifier_runner)
    result = build_result(
        access_authorization=auth,
        package_manifest=package,
        admission=admission,
        fact_set=fact_set,
        operator_capture=operator_capture,
        research=research,
        certified=certified,
    )
    packet_md = build_decision_packet_markdown(
        access_authorization=auth,
        package_manifest=package,
        admission=admission,
        fact_set=fact_set,
        operator_capture=operator_capture,
        research=research,
        certified=certified,
    )

    auth_path = out_dir / "access_authorization.json"
    if auth_path.is_file():
        existing = _load_authority_json(
            auth_path, missing_code="ALPHA0_SF2_ACCESS_AUTHORIZATION_MISSING"
        )
        if existing.get("authorization_hash") != auth["authorization_hash"]:
            raise GvAlpha0Sf2Error("ALPHA0_SF2_AUTH_BANK_TAMPER")
    else:
        _atomic_write_json(auth_path, auth)

    _atomic_write_case_bundle(
        out_dir,
        {
            "package_manifest.json": package,
            "admission_result.json": admission,
            "fact_set.json": fact_set,
            "operator_decision_capture.json": operator_capture,
            "research_decision.json": research,
            "decision_packet.md": packet_md,
            "result.json": result,
        },
        promote_order=(
            "package_manifest.json",
            "admission_result.json",
            "fact_set.json",
            "operator_decision_capture.json",
            "research_decision.json",
            "decision_packet.md",
            "result.json",
        ),
    )

    publication: CurrentDecisionPublicationResult | None = None
    if publish:
        publication = publish_current_decision(
            certified,
            target=current_target or DEFAULT_CURRENT_DECISION_TARGET,
            lock_path=current_lock or DEFAULT_CURRENT_DECISION_LOCK,
        )

    return {
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "source_family_id": SOURCE_FAMILY_ID,
        "family_one_reference": FAMILY_ONE_ID,
        "accession": ACCESSION,
        "admission_status": admission["status"],
        "admission_hash": admission["admission_hash"],
        "fact_set_hash": fact_set["fact_set_hash"],
        "fact_count": fact_set["fact_count"],
        "operator_capture_hash": operator_capture["operator_capture_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "decision_id": DECISION_ID,
        "rationale_ref": research["rationale_ref"],
        "certification_status": certified["certification"]["certification_status"],
        "certified_decision_result_hash": certified.get(
            "certified_decision_result_hash"
        ),
        "result_hash": result["result_hash"],
        "shipped_product_score": 39,
        "observed_comparison_count": 0,
        "real_external_source_packages_processed": 1,
        "data_admission_certificates_earned": 1,
        "reconciliation_status": "NOT_RUN",
        "formal_comparison_status": "DEFERRED_AFTER_ALPHA",
        "published": publication is not None,
        "independent_source_count": 1,
    }


if __name__ == "__main__":
    out = run_v2_alpha0_source_family_two(publish=False)
    print(json.dumps(out, indent=2, sort_keys=True))
