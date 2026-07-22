"""GV-V2-B0B official-source intake — one MU SEC accession, fail-closed.

Classification:

  GV-V2-B0B-OFFICIAL-SOURCE-INTAKE

Vertical:

  pre-read detached DataAccessAuthorization (remote before fetch)
  → exact three EDGAR objects (index, complete submission, primary 10-Q)
  → relational package_manifest (receipt time lives here, not in auth)
  → PIT/custody admission (ADMITTED | BLOCKED) + optional certificate
  → separate claim evaluation (SUFFICIENT_FOR_RESEARCH_TRIAGE |
      CLAIM_INSUFFICIENT | CLAIM_CONTRADICTED | NOT_EVALUABLE)
  → research ADVANCE | HOLD | REJECT
  → DecisionEnvelope → PortfolioBook → Fs0Certification
  → visible paper NO_POSITION

Hard rules:
  ADMITTED never auto-ADVANCE
  contradiction status is PASS | FAIL | NOT_EVALUATED (not nullable bool)
  independent_source_count = 1 (three objects are custody redundancy)
  score stays 39; observed stays 0
  B0A bank untouched
"""

from __future__ import annotations

import json
import re
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

CASE_ID = "V2_B0B_MU_G_SUPPLY_OFFICIAL_SOURCE_1"
SUBJECT = "MU"
MODULE = "G_supply"
DECISION_ID = "DECISION_V2_B0B_MU_G_SUPPLY_1"
SLICE_CLASSIFICATION = "GV-V2-B0B-OFFICIAL-SOURCE-INTAKE"
SOURCE_FAMILY_ID = "SEC:0000723125-26-000015"
ACCESSION = "0000723125-26-000015"
CIK = "0000723125"
FORM = "10-Q"

RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
RESEARCH_ACTION_ADVANCE = "ADVANCE_TO_FULL_RESEARCH"
RESEARCH_ACTION_REJECT = "REJECT_THESIS"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"

CLAIM_SUFFICIENT = "SUFFICIENT_FOR_RESEARCH_TRIAGE"
CLAIM_INSUFFICIENT = "CLAIM_INSUFFICIENT"
CLAIM_CONTRADICTED = "CLAIM_CONTRADICTED"
CLAIM_NOT_EVALUABLE = "NOT_EVALUABLE"

CONTRADICTION_PASS = "PASS"
CONTRADICTION_FAIL = "FAIL"
CONTRADICTION_NOT_EVALUATED = "NOT_EVALUATED"

ACCESS_AUTH_SCHEMA = "gv_v2_b0b_data_access_authorization_v1"
PACKAGE_MANIFEST_SCHEMA = "gv_v2_b0b_package_manifest_v1"
SOURCE_MANIFEST_SCHEMA = "gv_v2_b0b_source_manifest_v1"
ADMISSION_SCHEMA = "gv_v2_b0b_admission_result_v1"
CLAIM_SCHEMA = "gv_v2_b0b_claim_evaluation_v1"
RESEARCH_SCHEMA = "gv_v2_b0b_research_decision_v1"
RESULT_SCHEMA = "gv_v2_b0b_result_v1"

ACCESS_AUTH_DOMAIN = "GV-V2-B0B:DATA_ACCESS_AUTH:V1"
PACKAGE_MANIFEST_DOMAIN = "GV-V2-B0B:PACKAGE_MANIFEST:V1"
SOURCE_MANIFEST_DOMAIN = "GV-V2-B0B:SOURCE_MANIFEST:V1"
ADMISSION_DOMAIN = "GV-V2-B0B:ADMISSION:V1"
CERTIFICATE_DOMAIN = "GV-V2-B0B:ADMISSION_CERTIFICATE:V1"
CLAIM_DOMAIN = "GV-V2-B0B:CLAIM_EVALUATION:V1"
RESEARCH_DOMAIN = "GV-V2-B0B:RESEARCH_DECISION:V1"
RESULT_DOMAIN = "GV-V2-B0B:RESULT:V1"

RATIONALE_REF_PREFIX = "V2B0B:CLM:"

DEFAULT_CASE_DIR = ROOT / "data" / "gv_v2_b0b" / "mu_0000723125-26-000015"
DEFAULT_RAW_DIR = DEFAULT_CASE_DIR / "raw"
DEFAULT_ACCESS_AUTH_PATH = DEFAULT_CASE_DIR / "access_authorization.json"
DEFAULT_PACKAGE_MANIFEST_PATH = DEFAULT_CASE_DIR / "package_manifest.json"
DEFAULT_SOURCE_MANIFEST_PATH = DEFAULT_CASE_DIR / "source_manifest.json"
DEFAULT_ADMISSION_PATH = DEFAULT_CASE_DIR / "admission_result.json"
DEFAULT_CLAIM_PATH = DEFAULT_CASE_DIR / "claim_evaluation.json"
DEFAULT_RESEARCH_PATH = DEFAULT_CASE_DIR / "research_decision.json"
DEFAULT_RESULT_PATH = DEFAULT_CASE_DIR / "result.json"
DEFAULT_DECISION_PACKET_PATH = DEFAULT_CASE_DIR / "decision_packet.md"

# Exact three objects — no equivalents.
PACKAGE_OBJECTS: tuple[dict[str, str], ...] = (
    {
        "role": "accession_index",
        "filename": "0000723125-26-000015-index.htm",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/723125/"
            "000072312526000015/0000723125-26-000015-index.htm"
        ),
        "expected_sha256": (
            "b54139412d4ec15eca5185e06a26873793fd9203b5ab9a2b23bf8f135604d246"
        ),
        "expected_byte_length": "12770",
    },
    {
        "role": "complete_submission",
        "filename": "0000723125-26-000015.txt",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/723125/"
            "000072312526000015/0000723125-26-000015.txt"
        ),
        "expected_sha256": (
            "06448b1a5e3002c2c7d634becaa55dc4e4ae32c8e6b73aeb16fc143ae651fbc2"
        ),
        "expected_byte_length": "7981549",
    },
    {
        "role": "primary_10q",
        "filename": "mu-20260528.htm",
        "official_locator": (
            "https://www.sec.gov/Archives/edgar/data/723125/"
            "000072312526000015/mu-20260528.htm"
        ),
        "expected_sha256": (
            "bf4c3fb1833243d1c41c0426c4e0332d3a2f61a2b44e534fe8ff13648f205e20"
        ),
        "expected_byte_length": "1531708",
    },
)

EXPECTED_AUTH_HASH = (
    "23b18294536ed132e206989922b5102527b3123decbc03521e3a1989374bdd8d"
)
PURPOSE = "GV_V2_B0B_OFFICIAL_SOURCE_INTAKE_MU_G_SUPPLY_ONE_ACCESSION"
AUTH_PROVENANCE = "OWNER_REVISE_AND_GO_AUDIT_PRE_READ_B0B"

# Fixed receipt times from the post-authorization fetch (auth_at < all retrieved_at).
# Normalized to GV-FS0 six-digit fractional seconds.
PINNED_RETRIEVED_AT: dict[str, str] = {
    "0000723125-26-000015-index.htm": "2026-07-22T17:22:32.803000Z",
    "0000723125-26-000015.txt": "2026-07-22T17:22:37.848000Z",
    "mu-20260528.htm": "2026-07-22T17:22:39.732000Z",
}
PACKAGE_RETRIEVED_AT = "2026-07-22T17:22:39.732000Z"
RETRIEVAL_METHOD = "https_get_sec_edgar_user_agent_declared"

CLAIM_BOUNDARY = (
    "V2-B0B official-source intake for one MU G_supply SEC accession. "
    "Certified paper decision only. No established mispricing, alpha, "
    "investability, tradability, trade recommendation, score uplift, or "
    "general decision improvement claim. ADMITTED never auto-advances research. "
    "One company filing is not independent corroboration. "
    "SUFFICIENT_FOR_RESEARCH_TRIAGE does not mean thesis true, physical supply "
    "identified, issuer claims corroborated, investment justified, or position open."
)

# Stable needles in primary 10-Q for statement extraction (exact byte windows).
CLAIM_NEEDLES: tuple[dict[str, str], ...] = (
    {
        "statement_id": "B0B_STMT_SUPPLY_ALLOCATION_001",
        "needle": "decisions on supply allocation",
        "statement_class": "ISSUER_ASSERTION",
        "section_locator": "MD&A / Overview (primary 10-Q body)",
        "window_before": "80",
        "window_after": "160",
    },
    {
        "statement_id": "B0B_STMT_CONSTRAINED_SUPPLY_001",
        "needle": "constrained supply has led to increased pricing",
        "statement_class": "ISSUER_ASSERTION",
        "section_locator": "MD&A / Overview (primary 10-Q body)",
        "window_before": "80",
        "window_after": "120",
    },
    {
        "statement_id": "B0B_STMT_DEMAND_EXCEEDS_SUPPLY_001",
        "needle": "exceeds overall industry supply",
        "statement_class": "ISSUER_ASSERTION",
        "section_locator": "MD&A / Overview (primary 10-Q body)",
        "window_before": "80",
        "window_after": "100",
    },
    {
        "statement_id": "B0B_STMT_TAIWAN_FAB_001",
        "needle": "Tongluo, Miaoli County, Taiwan",
        "statement_class": "FINANCIAL_FACT",
        "section_locator": "Notes / facility acquisition disclosure",
        "window_before": "60",
        "window_after": "140",
    },
    {
        "statement_id": "B0B_STMT_SINGAPORE_EXPANSION_001",
        "needle": "expansion of our Singapore manufacturing",
        "statement_class": "CONTRACTUAL_DISCLOSURE",
        "section_locator": "Notes / manufacturing expansion incentives",
        "window_before": "60",
        "window_after": "140",
    },
)


class GvV2B0BError(RuntimeError):
    """Fail-closed V2-B0B official-source intake error."""


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


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _require_file(path: Path, code: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise GvV2B0BError(code)
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
        raise GvV2B0BError(f"V2B0B_WRITE_VERIFY_FAILED:{path.name}")
    return sha256(raw).hexdigest()


def _parse_ts(value: str) -> str:
    """Normalize timestamps to six fractional digits for ordering compares."""
    text = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", text):
        return text
    m = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{1,6})Z", text
    )
    if m:
        frac = m.group(2).ljust(6, "0")
        return f"{m.group(1)}.{frac}Z"
    m2 = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z", text)
    if m2:
        return f"{m2.group(1)}.000000Z"
    raise GvV2B0BError(f"V2B0B_TIMESTAMP_INVALID:{text}")


def _assert_auth_before_receipt(auth_at: str, retrieved_at: str) -> None:
    a = _parse_ts(auth_at)
    r = _parse_ts(retrieved_at)
    if not (a < r):
        raise GvV2B0BError(
            f"V2B0B_AUTH_RECEIPT_ORDERING_INVALID:auth={a}:retrieved={r}"
        )


def _body_without_hash(payload: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    return {k: v for k, v in _plain(payload).items() if k != hash_key}


def recompute_domain_hash(
    domain: str, payload: Mapping[str, Any], hash_key: str
) -> str:
    """Recompute domain hash from complete body excluding the hash field itself."""

    return domain_hash(domain, _body_without_hash(payload, hash_key))


def require_domain_hash(
    payload: Mapping[str, Any],
    *,
    domain: str,
    hash_key: str,
    error_code: str,
) -> str:
    """Fail closed when a stored domain hash does not match the recomputed body."""

    stored = payload.get(hash_key)
    recomputed = recompute_domain_hash(domain, payload, hash_key)
    if stored != recomputed:
        raise GvV2B0BError(error_code)
    return str(recomputed)


def _header_field(header_text: str, label: str) -> str:
    # SEC complete-submission headers use either SGML tags or "LABEL:value".
    m = re.search(
        rf"(?:<{re.escape(label)}>([^\r\n<]+)|{re.escape(label)}\s*:\s*([^\r\n]+))",
        header_text,
    )
    if not m:
        raise GvV2B0BError(f"V2B0B_SEC_HEADER_FIELD_MISSING:{label}")
    return (m.group(1) or m.group(2) or "").strip()


def _acceptance_datetime_to_iso(raw: str) -> str:
    """Map SEC ACCEPTANCE-DATETIME YYYYMMDDHHMMSS → UTC ISO with six fractional digits."""

    text = raw.strip()
    if not re.fullmatch(r"\d{14}", text):
        raise GvV2B0BError(f"V2B0B_SEC_ACCEPTANCE_DATETIME_INVALID:{text}")
    return (
        f"{text[0:4]}-{text[4:6]}-{text[6:8]}T"
        f"{text[8:10]}:{text[10:12]}:{text[12:14]}.000000Z"
    )


def _yyyymmdd_to_iso_date(raw: str) -> str:
    text = raw.strip()
    if not re.fullmatch(r"\d{8}", text):
        raise GvV2B0BError(f"V2B0B_SEC_DATE_INVALID:{text}")
    return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"


def parse_sec_complete_submission_header(data: bytes) -> dict[str, str]:
    """Parse identity/PIT fields from one exact SEC complete-submission package.

    Narrow parser for this accession format only — not a provider framework.
    """

    # Header is small; cap decode window to avoid loading multi-MB body for metadata.
    window = data[: min(len(data), 256_000)].decode("utf-8", errors="replace")
    end = window.find("</SEC-HEADER>")
    if end < 0:
        raise GvV2B0BError("V2B0B_SEC_HEADER_MISSING")
    header = window[:end]

    accession = _header_field(header, "ACCESSION NUMBER")
    form = _header_field(header, "CONFORMED SUBMISSION TYPE")
    period = _header_field(header, "CONFORMED PERIOD OF REPORT")
    filed = _header_field(header, "FILED AS OF DATE")
    cik = _header_field(header, "CENTRAL INDEX KEY")
    acceptance_raw = _header_field(header, "ACCEPTANCE-DATETIME")

    # First primary document of TYPE 10-Q in the submission stream.
    primary_match = re.search(
        r"<TYPE>\s*10-Q\s*<SEQUENCE>\s*\d+\s*<FILENAME>\s*([^\r\n<]+)",
        window,
        flags=re.IGNORECASE,
    )
    if not primary_match:
        raise GvV2B0BError("V2B0B_SEC_PRIMARY_FILENAME_MISSING")
    primary_filename = primary_match.group(1).strip()

    company_match = re.search(
        r"COMPANY CONFORMED NAME:\s*([^\r\n]+)", header
    )
    company_name = (
        company_match.group(1).strip() if company_match else "Micron Technology, Inc."
    )

    return {
        "accession": accession,
        "cik": cik,
        "form": form,
        "acceptance_datetime_raw": acceptance_raw,
        "acceptance_datetime": _acceptance_datetime_to_iso(acceptance_raw),
        "period_ended": _yyyymmdd_to_iso_date(period),
        "filed_at": _yyyymmdd_to_iso_date(filed),
        "primary_document_filename": primary_filename,
        "company_name": company_name,
    }


def parse_sec_accession_index_primary(data: bytes) -> dict[str, str]:
    """Derive primary 10-Q filename from the accession index HTML bytes."""

    text = data.decode("utf-8", errors="replace")
    # Index table row: Type 10-Q document link to mu-20260528.htm
    m = re.search(
        r'href="[^"]*?(mu-20260528\.htm)"[^>]*>\s*mu-20260528\.htm',
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        # Fallback: any 10-Q cell followed by the primary htm name.
        m2 = re.search(
            r">\s*10-Q\s*<.*?>\s*<a[^>]+>(mu-20260528\.htm)</a>",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not m2:
            raise GvV2B0BError("V2B0B_INDEX_PRIMARY_FILENAME_MISSING")
        primary = m2.group(1).strip()
    else:
        primary = m.group(1).strip()

    acc = re.search(r"0000723125-26-000015", text)
    if not acc:
        raise GvV2B0BError("V2B0B_INDEX_ACCESSION_MISSING")
    return {
        "accession": ACCESSION,
        "primary_document_filename": primary,
        "form": FORM,
    }


def derive_sec_package_identity(*, root: Path) -> dict[str, str]:
    """Cross-check complete submission header ↔ accession index ↔ package pins."""

    raw_dir = root / "data/gv_v2_b0b/mu_0000723125-26-000015/raw"
    complete_path = _require_file(
        raw_dir / "0000723125-26-000015.txt",
        "V2B0B_PACKAGE_OBJECT_MISSING:0000723125-26-000015.txt",
    )
    index_path = _require_file(
        raw_dir / "0000723125-26-000015-index.htm",
        "V2B0B_PACKAGE_OBJECT_MISSING:0000723125-26-000015-index.htm",
    )
    primary_path = _require_file(
        raw_dir / "mu-20260528.htm",
        "V2B0B_PACKAGE_OBJECT_MISSING:mu-20260528.htm",
    )

    header = parse_sec_complete_submission_header(complete_path.read_bytes())
    index = parse_sec_accession_index_primary(index_path.read_bytes())

    if header["accession"] != ACCESSION or index["accession"] != ACCESSION:
        raise GvV2B0BError("V2B0B_SOURCE_DERIVED_ACCESSION_MISMATCH")
    if header["cik"] != CIK:
        raise GvV2B0BError("V2B0B_SOURCE_DERIVED_CIK_MISMATCH")
    if header["form"] != FORM:
        raise GvV2B0BError("V2B0B_SOURCE_DERIVED_FORM_MISMATCH")
    if header["primary_document_filename"] != "mu-20260528.htm":
        raise GvV2B0BError("V2B0B_SOURCE_DERIVED_PRIMARY_MISMATCH")
    if index["primary_document_filename"] != "mu-20260528.htm":
        raise GvV2B0BError("V2B0B_INDEX_PRIMARY_MISMATCH")
    if not primary_path.is_file():
        raise GvV2B0BError("V2B0B_PRIMARY_OBJECT_MISSING")
    # Primary object role pin must match submission-identified primary document.
    primary_spec = PACKAGE_OBJECTS[2]
    if primary_spec["filename"] != header["primary_document_filename"]:
        raise GvV2B0BError("V2B0B_PACKAGE_PRIMARY_ROLE_MISMATCH")
    return header


def load_access_authorization(*, root: Path | None = None) -> dict[str, Any]:
    """Load the remotely retained pre-read authorization object."""

    base = Path(root) if root is not None else ROOT
    path = _require_file(
        base / "data/gv_v2_b0b/mu_0000723125-26-000015/access_authorization.json",
        "V2B0B_ACCESS_AUTHORIZATION_MISSING",
    )
    auth = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(auth, dict):
        raise GvV2B0BError("V2B0B_ACCESS_AUTHORIZATION_NOT_OBJECT")
    if auth.get("retrieval_or_receipt_time") is not None:
        raise GvV2B0BError("V2B0B_AUTH_MUST_NOT_CONTAIN_RECEIPT_TIME")
    if auth.get("accession") != ACCESSION:
        raise GvV2B0BError("V2B0B_AUTH_ACCESSION_MISMATCH")
    if auth.get("cik") != CIK:
        raise GvV2B0BError("V2B0B_AUTH_CIK_MISMATCH")
    if auth.get("form") != FORM:
        raise GvV2B0BError("V2B0B_AUTH_FORM_MISMATCH")
    if auth.get("purpose") != PURPOSE:
        raise GvV2B0BError("V2B0B_AUTH_PURPOSE_MISMATCH")
    body = {k: v for k, v in auth.items() if k != "authorization_hash"}
    recomputed = domain_hash(ACCESS_AUTH_DOMAIN, body)
    if auth.get("authorization_hash") != recomputed:
        raise GvV2B0BError("V2B0B_AUTH_HASH_MISMATCH")
    if recomputed != EXPECTED_AUTH_HASH:
        raise GvV2B0BError("V2B0B_AUTH_HASH_NOT_PINNED")
    if "password" in json.dumps(auth).lower() and "none" not in str(
        auth.get("credentials_boundary", "")
    ).lower():
        raise GvV2B0BError("V2B0B_CREDENTIALS_PROHIBITED")
    return auth


def build_package_manifest(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Relational package manifest with retrieval receipt fields."""

    base = Path(root) if root is not None else ROOT
    auth = (
        _plain(access_authorization)
        if access_authorization is not None
        else load_access_authorization(root=base)
    )
    raw_dir = base / "data/gv_v2_b0b/mu_0000723125-26-000015/raw"
    objects: list[dict[str, Any]] = []
    for spec in PACKAGE_OBJECTS:
        filename = spec["filename"]
        path = _require_file(raw_dir / filename, f"V2B0B_PACKAGE_OBJECT_MISSING:{filename}")
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        if digest != spec["expected_sha256"]:
            raise GvV2B0BError(f"V2B0B_PACKAGE_HASH_MISMATCH:{filename}")
        if str(len(data)) != spec["expected_byte_length"]:
            raise GvV2B0BError(f"V2B0B_PACKAGE_LENGTH_MISMATCH:{filename}")
        retrieved_at = PINNED_RETRIEVED_AT[filename]
        _assert_auth_before_receipt(
            str(auth["authorization_recorded_at"]), retrieved_at
        )
        objects.append(
            {
                "role": spec["role"],
                "filename": filename,
                "relative_path": f"data/gv_v2_b0b/mu_0000723125-26-000015/raw/{filename}",
                "official_locator": spec["official_locator"],
                "accession": ACCESSION,
                "sha256": digest,
                "byte_length": len(data),
                "response_sha256": digest,
                "response_byte_length": len(data),
                "retrieved_at": retrieved_at,
            }
        )

    body = {
        "schema_version": PACKAGE_MANIFEST_SCHEMA,
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "accession": ACCESSION,
        "cik": CIK,
        "form": FORM,
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "access_authorization_hash": auth["authorization_hash"],
        "authorization_recorded_at": auth["authorization_recorded_at"],
        "retrieved_at": PACKAGE_RETRIEVED_AT,
        "retrieval_method": RETRIEVAL_METHOD,
        "source_locator": (
            "https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/"
        ),
        "objects": objects,
        "object_roles": [o["role"] for o in objects],
        "custody_note": (
            "Index, complete submission, and primary 10-Q are overlapping "
            "representations of one SEC accession (custody redundancy). "
            "They are not three independent evidence sources."
        ),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["package_manifest_hash"] = domain_hash(PACKAGE_MANIFEST_DOMAIN, body)
    return body


def build_source_manifest(
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
    # Pre-read authorization identity must match package pins before source derivation.
    if auth.get("accession") != ACCESSION:
        raise GvV2B0BError("V2B0B_AUTH_ACCESSION_MISMATCH")
    if auth.get("cik") != CIK:
        raise GvV2B0BError("V2B0B_AUTH_CIK_MISMATCH")
    if auth.get("form") != FORM:
        raise GvV2B0BError("V2B0B_AUTH_FORM_MISMATCH")
    require_domain_hash(
        auth,
        domain=ACCESS_AUTH_DOMAIN,
        hash_key="authorization_hash",
        error_code="V2B0B_AUTH_HASH_MISMATCH",
    )

    package = (
        _plain(package_manifest)
        if package_manifest is not None
        else build_package_manifest(root=base, access_authorization=auth)
    )
    require_domain_hash(
        package,
        domain=PACKAGE_MANIFEST_DOMAIN,
        hash_key="package_manifest_hash",
        error_code="V2B0B_PACKAGE_MANIFEST_HASH_MISMATCH",
    )
    if package.get("accession") != ACCESSION or package.get("cik") != CIK:
        raise GvV2B0BError("V2B0B_PACKAGE_IDENTITY_MISMATCH")
    if package.get("form") != FORM:
        raise GvV2B0BError("V2B0B_PACKAGE_FORM_MISMATCH")
    if package.get("access_authorization_hash") != auth.get("authorization_hash"):
        raise GvV2B0BError("V2B0B_AUTH_PACKAGE_BINDING_INVALID")

    # Source-derived PIT/identity from complete submission + index cross-check.
    derived = derive_sec_package_identity(root=base)
    if derived["accession"] != auth.get("accession"):
        raise GvV2B0BError("V2B0B_AUTH_HEADER_ACCESSION_MISMATCH")
    if derived["cik"] != auth.get("cik"):
        raise GvV2B0BError("V2B0B_AUTH_HEADER_CIK_MISMATCH")
    if derived["form"] != auth.get("form"):
        raise GvV2B0BError("V2B0B_AUTH_HEADER_FORM_MISMATCH")
    if derived["accession"] != package.get("accession"):
        raise GvV2B0BError("V2B0B_PACKAGE_HEADER_ACCESSION_MISMATCH")

    files = [
        {
            "path": obj["relative_path"],
            "sha256": obj["sha256"],
            "byte_length": obj["byte_length"],
            "role": obj["role"],
            "official_locator": obj["official_locator"],
        }
        for obj in package["objects"]
    ]
    body = {
        "schema_version": SOURCE_MANIFEST_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "slice_classification": SLICE_CLASSIFICATION,
        "accession": derived["accession"],
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "access_authorization_hash": auth["authorization_hash"],
        "package_manifest_hash": package["package_manifest_hash"],
        "files": files,
        "publication_time": derived["acceptance_datetime"],
        "known_at": derived["acceptance_datetime"],
        "effective_period": {
            "period_ended": derived["period_ended"],
            "accepted_at": derived["acceptance_datetime"],
            "filed_at": derived["filed_at"],
        },
        "revision_or_vintage_state": f"sec_10q_accession_{derived['accession']}",
        "units": None,
        "entity_identity": {
            "ticker": "MU",
            "company_name": "Micron Technology, Inc.",
            "cik": derived["cik"],
            "identity_source": SOURCE_FAMILY_ID,
            "primary_document_filename": derived["primary_document_filename"],
            "source_derived": True,
        },
        "source_derived_pit": {
            "acceptance_datetime_raw": derived["acceptance_datetime_raw"],
            "acceptance_datetime": derived["acceptance_datetime"],
            "period_ended": derived["period_ended"],
            "filed_at": derived["filed_at"],
            "primary_document_filename": derived["primary_document_filename"],
            "derivation": "complete_submission_header_and_accession_index",
        },
        "upstream_duplication": "single_sec_accession_three_custody_objects",
        "point_in_time_available": True,
        "real_physical_supply_bytes_present": False,
        "official_company_filing_bytes_present": True,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["source_manifest_hash"] = domain_hash(SOURCE_MANIFEST_DOMAIN, body)
    return body


def run_admission_checks(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any] | None = None,
    package_manifest: Mapping[str, Any] | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed admission: ADMITTED only when all checks pass; else BLOCKED."""

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
    manifest = (
        _plain(source_manifest)
        if source_manifest is not None
        else build_source_manifest(
            root=base, access_authorization=auth, package_manifest=package
        )
    )
    if package.get("access_authorization_hash") != auth.get("authorization_hash"):
        raise GvV2B0BError("V2B0B_AUTH_PACKAGE_BINDING_INVALID")
    if manifest.get("access_authorization_hash") != auth.get("authorization_hash"):
        raise GvV2B0BError("V2B0B_AUTH_MANIFEST_BINDING_INVALID")
    if manifest.get("package_manifest_hash") != package.get("package_manifest_hash"):
        raise GvV2B0BError("V2B0B_PACKAGE_SOURCE_MANIFEST_BINDING_INVALID")

    checks: dict[str, dict[str, Any]] = {}
    blocks: list[str] = []

    # 1) Licence / permitted use
    permitted = set(auth.get("permitted_use") or [])
    forbidden = set(auth.get("forbidden_use") or [])
    licence_ok = (
        "official_raw_package_custody" in permitted
        and "v2_b0b_admission_evaluation" in permitted
        and "automatic_research_advancement" in forbidden
        and "synthetic_as_real_evidence" in forbidden
        and "count_index_primary_submission_as_independent_corroborators" in forbidden
    )
    checks["licence_and_permitted_use"] = {
        "pass": licence_ok,
        "detail": (
            "Access auth permits official raw custody + admission eval; "
            "auto-advance and multi-object corroboration banned."
            if licence_ok
            else "Licence/permitted-use checks failed."
        ),
    }
    if not licence_ok:
        blocks.append("LICENCE_NOT_AUTHORIZED")

    # 2) Point-in-time availability — must be source-derived, not free constants.
    require_domain_hash(
        manifest,
        domain=SOURCE_MANIFEST_DOMAIN,
        hash_key="source_manifest_hash",
        error_code="V2B0B_SOURCE_MANIFEST_HASH_MISMATCH",
    )
    derived_pit = manifest.get("source_derived_pit")
    period = manifest.get("effective_period")
    pit_ok = (
        manifest.get("point_in_time_available") is True
        and isinstance(derived_pit, Mapping)
        and isinstance(period, Mapping)
        and manifest.get("known_at") == derived_pit.get("acceptance_datetime")
        and manifest.get("publication_time") == derived_pit.get("acceptance_datetime")
        and period.get("accepted_at") == derived_pit.get("acceptance_datetime")
        and period.get("period_ended") == derived_pit.get("period_ended")
        and period.get("filed_at") == derived_pit.get("filed_at")
        and derived_pit.get("primary_document_filename") == "mu-20260528.htm"
        and (manifest.get("entity_identity") or {}).get("cik") == CIK
        and manifest.get("accession") == ACCESSION
    )
    checks["point_in_time_availability"] = {
        "pass": pit_ok,
        "detail": (
            "SEC acceptance/filing/period metadata derived from complete submission "
            "header and cross-checked to accession index + package + authorization."
            if pit_ok
            else "Missing or non-source-derived known_at/publication_time/effective_period."
        ),
    }
    if not pit_ok:
        blocks.append("MISSING_POINT_IN_TIME_AUTHORITY")

    # 3) Immutable byte identity + package relational binding
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
        if path.stat().st_size != int(item.get("byte_length") or -1):
            identity_ok = False
            identity_notes.append(f"length_mismatch:{rel}")

    binding_ok = True
    binding_notes: list[str] = []
    by_name = {o["filename"]: o for o in package.get("objects") or []}
    for spec in PACKAGE_OBJECTS:
        obj = by_name.get(spec["filename"])
        if obj is None:
            binding_ok = False
            binding_notes.append(f"missing_object:{spec['filename']}")
            continue
        if obj.get("official_locator") != spec["official_locator"]:
            binding_ok = False
            binding_notes.append(f"locator_mismatch:{spec['filename']}")
        if obj.get("accession") != ACCESSION:
            binding_ok = False
            binding_notes.append(f"accession_mismatch:{spec['filename']}")
        if obj.get("sha256") != spec["expected_sha256"]:
            binding_ok = False
            binding_notes.append(f"sha_mismatch:{spec['filename']}")
        if str(obj.get("byte_length")) != spec["expected_byte_length"]:
            binding_ok = False
            binding_notes.append(f"len_mismatch:{spec['filename']}")
        if obj.get("role") != spec["role"]:
            binding_ok = False
            binding_notes.append(f"role_mismatch:{spec['filename']}")

    checks["immutable_byte_identity"] = {
        "pass": identity_ok,
        "detail": "; ".join(identity_notes) if identity_notes else "exact hashes verified",
    }
    if not identity_ok:
        blocks.append("DATA_ABSTENTION")

    checks["package_manifest_binding"] = {
        "pass": binding_ok,
        "detail": (
            "; ".join(binding_notes)
            if binding_notes
            else "source→locator→role→sha256→length bound for three exact objects"
        ),
    }
    if not binding_ok:
        blocks.append("SOURCE_PACKAGE_MANIFEST_BINDING_INVALID")

    # 4) Auth/receipt temporal ordering
    try:
        _assert_auth_before_receipt(
            str(auth["authorization_recorded_at"]),
            str(package["retrieved_at"]),
        )
        temporal_ok = True
        temporal_detail = (
            f"authorization_recorded_at={auth['authorization_recorded_at']} < "
            f"retrieved_at={package['retrieved_at']}"
        )
    except GvV2B0BError as exc:
        temporal_ok = False
        temporal_detail = str(exc)
        blocks.append("AUTH_RECEIPT_ORDERING_INVALID")
    checks["authorization_before_retrieval"] = {
        "pass": temporal_ok,
        "detail": temporal_detail,
    }

    # 5) Semantic / schema for official filing admission
    has_filing = bool(manifest.get("official_company_filing_bytes_present"))
    has_physical = bool(manifest.get("real_physical_supply_bytes_present"))
    # Official filing present is sufficient for package admission; physical
    # telemetry absence is expected and recorded, not a semantic fail.
    semantic_ok = has_filing is True
    checks["semantic_and_schema_validity"] = {
        "pass": semantic_ok,
        "detail": (
            "Official company filing package present; physical supply telemetry "
            f"present={has_physical} (not required for filing admission)."
        ),
    }
    if not semantic_ok:
        blocks.append("INCOMPLETE_INDISPENSABLE_EVIDENCE")

    # 6) Completeness for package custody (not G_supply claim completeness)
    complete_ok = (
        semantic_ok
        and binding_ok
        and identity_ok
        and len(package.get("objects") or []) == 3
        and int(package.get("independent_source_count") or 0) == 1
    )
    checks["completeness"] = {
        "pass": complete_ok,
        "detail": (
            "Three exact custody objects banked under independent_source_count=1."
            if complete_ok
            else "Package custody incomplete."
        ),
    }
    if not complete_ok and "INCOMPLETE_INDISPENSABLE_EVIDENCE" not in blocks:
        blocks.append("INCOMPLETE_INDISPENSABLE_EVIDENCE")

    # 7) Contradictions among indispensable admitted facts — tri-state
    # No admitted indispensable claim-facts at admission layer (custody only)
    # → NOT_EVALUATED (not vacuous PASS).
    checks["contradictions"] = {
        "status": CONTRADICTION_NOT_EVALUATED,
        "pass": None,
        "detail": (
            "No admitted indispensable claim-level facts at admission layer; "
            "contradiction is NOT_EVALUATED (custody admission only)."
        ),
    }

    # 8) Purpose compatibility
    purpose_ok = str(auth.get("purpose") or "") == PURPOSE
    checks["purpose_compatibility"] = {
        "pass": purpose_ok,
        "detail": (
            "Purpose is official-source intake for one MU G_supply accession."
            if purpose_ok
            else f"Unexpected purpose: {auth.get('purpose')}"
        ),
    }
    if not purpose_ok:
        blocks.append("PURPOSE_INCOMPATIBLE")

    # 9) Forbidden-use enforcement
    forbidden_ok = (
        "automatic_research_advancement" in forbidden
        and "count_index_primary_submission_as_independent_corroborators" in forbidden
        and int(package.get("independent_source_count") or 0) == 1
    )
    checks["forbidden_use_enforcement"] = {
        "pass": forbidden_ok,
        "detail": (
            "Auto-advance banned; three objects counted as one source family."
            if forbidden_ok
            else "Forbidden-use enforcement failed."
        ),
    }
    if not forbidden_ok:
        blocks.append("DATA_ABSTENTION")

    # 10) Dedup authority
    dedup_ok = (
        package.get("source_family_id") == SOURCE_FAMILY_ID
        and manifest.get("source_family_id") == SOURCE_FAMILY_ID
        and int(package.get("independent_source_count") or 0) == 1
        and int(manifest.get("independent_source_count") or 0) == 1
    )
    checks["evidence_deduplication"] = {
        "pass": dedup_ok,
        "detail": (
            f"source_family_id={SOURCE_FAMILY_ID}; independent_source_count=1"
            if dedup_ok
            else "Evidence deduplication markers invalid."
        ),
    }
    if not dedup_ok:
        blocks.append("EVIDENCE_DEDUP_INVALID")

    hard_pass_keys = [
        k
        for k, v in checks.items()
        if k != "contradictions" and v.get("pass") is False
    ]
    admitted = not blocks and not hard_pass_keys

    certificate: dict[str, Any] | None = None
    if admitted:
        cert_body = {
            "schema_version": "gv_v2_b0b_data_admission_certificate_v1",
            "case_id": CASE_ID,
            "accession": ACCESSION,
            "source_family_id": SOURCE_FAMILY_ID,
            "access_authorization_hash": auth["authorization_hash"],
            "package_manifest_hash": package["package_manifest_hash"],
            "source_manifest_hash": manifest["source_manifest_hash"],
            "independent_source_count": 1,
            "admitted_object_roles": [o["role"] for o in package["objects"]],
            "claim_boundary": CLAIM_BOUNDARY,
            "alpha_claim": False,
            "certificate_note": (
                "Admission certifies official filing package custody only. "
                "Does not authorize research ADVANCE or portfolio position."
            ),
        }
        cert_body["admission_certificate_hash"] = domain_hash(
            CERTIFICATE_DOMAIN, cert_body
        )
        certificate = cert_body
        status = "ADMITTED"
        primary_block = None
        block_reasons: list[str] = []
    else:
        status = "BLOCKED"
        priority = (
            "AUTH_RECEIPT_ORDERING_INVALID",
            "SOURCE_PACKAGE_MANIFEST_BINDING_INVALID",
            "MISSING_POINT_IN_TIME_AUTHORITY",
            "LICENCE_NOT_AUTHORIZED",
            "PURPOSE_INCOMPATIBLE",
            "INCOMPLETE_INDISPENSABLE_EVIDENCE",
            "EVIDENCE_DEDUP_INVALID",
            "DATA_ABSTENTION",
        )
        present = set(blocks)
        primary_block = next((c for c in priority if c in present), "DATA_ABSTENTION")
        block_reasons = sorted(present)

    result_body: dict[str, Any] = {
        "schema_version": ADMISSION_SCHEMA,
        "case_id": CASE_ID,
        "status": status,
        "primary_block_reason": primary_block,
        "block_reasons": block_reasons,
        "checks": checks,
        "access_authorization_hash": auth["authorization_hash"],
        "package_manifest_hash": package["package_manifest_hash"],
        "source_manifest_hash": manifest["source_manifest_hash"],
        "admission_certificate": certificate,
        "slice_classification": SLICE_CLASSIFICATION,
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    result_body["admission_hash"] = domain_hash(ADMISSION_DOMAIN, result_body)
    return result_body


def _extract_statements(*, root: Path) -> list[dict[str, Any]]:
    primary_rel = (
        "data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm"
    )
    primary_path = _require_file(root / primary_rel, "V2B0B_PRIMARY_MISSING")
    data = primary_path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    source_hash = _sha256_bytes(data)
    statements: list[dict[str, Any]] = []
    for spec in CLAIM_NEEDLES:
        needle = spec["needle"]
        idx = text.find(needle)
        if idx < 0:
            raise GvV2B0BError(f"V2B0B_CLAIM_NEEDLE_MISSING:{spec['statement_id']}")
        before = int(spec["window_before"])
        after = int(spec["window_after"])
        start = max(0, idx - before)
        end = min(len(text), idx + len(needle) + after)
        excerpt = text[start:end]
        statements.append(
            {
                "statement_id": spec["statement_id"],
                "source_object_hash": source_hash,
                "document_locator": primary_rel,
                "official_locator": PACKAGE_OBJECTS[2]["official_locator"],
                "section_or_element_locator": spec["section_locator"],
                "byte_start": start,
                "byte_end": end,
                "exact_excerpt": excerpt,
                "exact_excerpt_hash": _sha256_bytes(excerpt.encode("utf-8")),
                "statement_class": spec["statement_class"],
                "source_family_id": SOURCE_FAMILY_ID,
                "independent_source_count_contribution": 0,
            }
        )
    return statements


def _verify_statement_locators(
    statements: list[dict[str, Any]], *, root: Path
) -> None:
    """Re-resolve each statement byte window against primary document bytes."""

    primary_rel = "data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm"
    primary_path = _require_file(root / primary_rel, "V2B0B_PRIMARY_MISSING")
    data = primary_path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    source_hash = _sha256_bytes(data)
    for stmt in statements:
        if stmt.get("source_object_hash") != source_hash:
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_SOURCE_HASH_MISMATCH:{stmt.get('statement_id')}"
            )
        start = int(stmt["byte_start"])
        end = int(stmt["byte_end"])
        if start < 0 or end > len(text) or start >= end:
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_LOCATOR_INVALID:{stmt.get('statement_id')}"
            )
        excerpt = text[start:end]
        if excerpt != stmt.get("exact_excerpt"):
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_EXCERPT_MISMATCH:{stmt.get('statement_id')}"
            )
        if _sha256_bytes(excerpt.encode("utf-8")) != stmt.get("exact_excerpt_hash"):
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_EXCERPT_HASH_MISMATCH:{stmt.get('statement_id')}"
            )
        if stmt.get("source_family_id") != SOURCE_FAMILY_ID:
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_SOURCE_FAMILY_MISMATCH:{stmt.get('statement_id')}"
            )
        contrib = stmt.get("independent_source_count_contribution")
        if contrib is None or int(contrib) != 0:
            raise GvV2B0BError(
                f"V2B0B_STATEMENT_INDEPENDENT_COUNT_INVALID:{stmt.get('statement_id')}"
            )


def evaluate_g_supply_claim(
    *,
    root: Path | None = None,
    admission: Mapping[str, Any] | None = None,
    package_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Separate claim evaluation — never inside admission pass.

    B0B uses an explicit narrow evidence-dimension rule. A positive
    SUFFICIENT_FOR_RESEARCH_TRIAGE outcome is not producible in this one-source
    slice (belongs to multi-source B0C).
    """

    base = Path(root) if root is not None else ROOT
    adm = _plain(admission) if admission is not None else run_admission_checks(root=base)
    package = (
        _plain(package_manifest)
        if package_manifest is not None
        else build_package_manifest(root=base)
    )

    require_domain_hash(
        adm,
        domain=ADMISSION_DOMAIN,
        hash_key="admission_hash",
        error_code="V2B0B_ADMISSION_HASH_MISMATCH",
    )
    require_domain_hash(
        package,
        domain=PACKAGE_MANIFEST_DOMAIN,
        hash_key="package_manifest_hash",
        error_code="V2B0B_PACKAGE_MANIFEST_HASH_MISMATCH",
    )
    cert = adm.get("admission_certificate")
    if isinstance(cert, Mapping) and cert:
        require_domain_hash(
            cert,
            domain=CERTIFICATE_DOMAIN,
            hash_key="admission_certificate_hash",
            error_code="V2B0B_ADMISSION_CERTIFICATE_HASH_MISMATCH",
        )

    if int(package.get("independent_source_count") or 0) != 1:
        raise GvV2B0BError("V2B0B_CLAIM_DEDUP_VIOLATION")
    if package.get("source_family_id") != SOURCE_FAMILY_ID:
        raise GvV2B0BError("V2B0B_CLAIM_SOURCE_FAMILY_MISMATCH")

    if adm.get("status") != "ADMITTED":
        body = {
            "schema_version": CLAIM_SCHEMA,
            "case_id": CASE_ID,
            "subject": SUBJECT,
            "module": MODULE,
            "slice_classification": SLICE_CLASSIFICATION,
            "admission_hash": adm["admission_hash"],
            "admission_status": adm.get("status"),
            "package_manifest_hash": package["package_manifest_hash"],
            "source_family_id": SOURCE_FAMILY_ID,
            "independent_source_count": 1,
            "claim_outcome": CLAIM_NOT_EVALUABLE,
            "evidence_dimensions": {
                "official_filing_admitted": "FAIL",
                "relevant_issuer_supply_assertions_present": "NOT_EVALUATED",
                "capacity_facility_disclosures_present": "NOT_EVALUATED",
                "independent_source_corroboration": "FAIL",
                "physical_supply_telemetry": "FAIL",
                "cross_source_contradiction_evaluation": "NOT_EVALUATED",
                "sufficient_for_research_advancement": "FAIL",
            },
            "statements": [],
            "evaluation_notes": [
                "Admission not ADMITTED; claim evaluation is NOT_EVALUABLE.",
            ],
            "contradiction_status": CONTRADICTION_NOT_EVALUATED,
            "alpha_claim": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        body["claim_evaluation_hash"] = domain_hash(CLAIM_DOMAIN, body)
        return body

    statements = _extract_statements(root=base)
    _verify_statement_locators(statements, root=base)
    classes = {s["statement_class"] for s in statements}
    issuer_assertions = [
        s for s in statements if s["statement_class"] == "ISSUER_ASSERTION"
    ]
    facility_disclosures = [
        s
        for s in statements
        if s["statement_class"] in {"FINANCIAL_FACT", "CONTRACTUAL_DISCLOSURE"}
    ]

    # Explicit B0B dimension rule (one-source slice only).
    dimensions = {
        "official_filing_admitted": "PASS",
        "relevant_issuer_supply_assertions_present": (
            "PASS" if len(issuer_assertions) >= 3 else "FAIL"
        ),
        "capacity_facility_disclosures_present": (
            "PASS" if len(facility_disclosures) >= 2 else "FAIL"
        ),
        "independent_source_corroboration": "FAIL",
        "physical_supply_telemetry": "FAIL",
        "cross_source_contradiction_evaluation": "NOT_EVALUATED",
        "sufficient_for_research_advancement": "FAIL",
    }
    # Derivation: independent corroboration absent OR physical identification
    # absent → CLAIM_INSUFFICIENT. B0B does not implement positive SUFFICIENT.
    if (
        dimensions["independent_source_corroboration"] != "PASS"
        or dimensions["physical_supply_telemetry"] != "PASS"
        or dimensions["sufficient_for_research_advancement"] != "PASS"
    ):
        outcome = CLAIM_INSUFFICIENT
    else:
        # Unreachable in B0B one-source rule; refuse speculative positive logic.
        raise GvV2B0BError("V2B0B_SUFFICIENT_CLAIM_NOT_AUTHORIZED_IN_B0B")

    notes = [
        "Evidence dimensions evaluated under B0B one-source rule.",
        f"official_filing_admitted={dimensions['official_filing_admitted']}",
        f"relevant_issuer_supply_assertions_present="
        f"{dimensions['relevant_issuer_supply_assertions_present']} "
        f"(count={len(issuer_assertions)})",
        f"capacity_facility_disclosures_present="
        f"{dimensions['capacity_facility_disclosures_present']} "
        f"(count={len(facility_disclosures)})",
        "independent_source_corroboration=FAIL (independent_source_count=1)",
        "physical_supply_telemetry=FAIL (real_physical_supply_bytes_present=false)",
        "cross_source_contradiction_evaluation=NOT_EVALUATED",
        "sufficient_for_research_advancement=FAIL",
        "Derivation: independent corroboration absent OR physical identification "
        "absent → CLAIM_INSUFFICIENT.",
        f"Statement classes observed: {sorted(classes)}.",
    ]
    contradiction_status = CONTRADICTION_NOT_EVALUATED

    body = {
        "schema_version": CLAIM_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "slice_classification": SLICE_CLASSIFICATION,
        "admission_hash": adm["admission_hash"],
        "admission_status": adm.get("status"),
        "admission_certificate_hash": (
            (adm.get("admission_certificate") or {}).get("admission_certificate_hash")
        ),
        "package_manifest_hash": package["package_manifest_hash"],
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "claim_outcome": outcome,
        "evidence_dimensions": dimensions,
        "statements": statements,
        "evaluation_notes": notes,
        "contradiction_status": contradiction_status,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["claim_evaluation_hash"] = domain_hash(CLAIM_DOMAIN, body)
    return body


def build_g_supply_research_decision(
    admission: Mapping[str, Any],
    claim: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Map admission + claim → research action.

    B0B refuses SUFFICIENT→ADVANCE (no speculative positive path). Every
    consuming boundary recomputes domain hashes before reading semantic fields.
    """

    admission = _plain(admission)
    claim = _plain(claim)
    base = Path(root) if root is not None else ROOT

    require_domain_hash(
        admission,
        domain=ADMISSION_DOMAIN,
        hash_key="admission_hash",
        error_code="V2B0B_ADMISSION_HASH_MISMATCH",
    )
    require_domain_hash(
        claim,
        domain=CLAIM_DOMAIN,
        hash_key="claim_evaluation_hash",
        error_code="V2B0B_CLAIM_EVALUATION_HASH_MISMATCH",
    )
    cert = admission.get("admission_certificate")
    if isinstance(cert, Mapping) and cert:
        require_domain_hash(
            cert,
            domain=CERTIFICATE_DOMAIN,
            hash_key="admission_certificate_hash",
            error_code="V2B0B_ADMISSION_CERTIFICATE_HASH_MISMATCH",
        )
        if claim.get("admission_certificate_hash") != cert.get(
            "admission_certificate_hash"
        ):
            raise GvV2B0BError("V2B0B_CLAIM_CERTIFICATE_BINDING_INVALID")

    if claim.get("admission_hash") != admission.get("admission_hash"):
        raise GvV2B0BError("V2B0B_CLAIM_ADMISSION_BINDING_INVALID")
    if claim.get("package_manifest_hash") != admission.get("package_manifest_hash"):
        raise GvV2B0BError("V2B0B_CLAIM_PACKAGE_BINDING_INVALID")
    if claim.get("source_family_id") != SOURCE_FAMILY_ID:
        raise GvV2B0BError("V2B0B_CLAIM_SOURCE_FAMILY_MISMATCH")
    if int(claim.get("independent_source_count") or 0) != 1:
        raise GvV2B0BError("V2B0B_CLAIM_DEDUP_VIOLATION")

    statements = list(claim.get("statements") or [])
    if statements:
        _verify_statement_locators(statements, root=base)

    adm_status = admission.get("status")
    claim_outcome = claim.get("claim_outcome")

    # B0B one-source slice: no ADVANCE and no REJECT path.
    # SUFFICIENT / CONTRADICTED belong to multi-source B0C; rehashed semantic
    # fields must not open speculative research actions here.
    if claim_outcome in {CLAIM_SUFFICIENT, CLAIM_CONTRADICTED}:
        raise GvV2B0BError(
            f"V2B0B_CLAIM_OUTCOME_NOT_AUTHORIZED_IN_B0B:{claim_outcome}"
        )
    if adm_status == "ADMITTED" and claim_outcome == CLAIM_INSUFFICIENT:
        research_action = RESEARCH_ACTION_HOLD
        rationale = (
            "Admission ADMITTED for official MU 10-Q package "
            f"{ACCESSION}, but claim evaluation is CLAIM_INSUFFICIENT: one issuer "
            "filing is not independent corroboration of physical supply inertia. "
            "HOLD_FOR_EVIDENCE is the correct research triage. "
            "ADMITTED does not auto-advance research."
        )
    elif claim_outcome in {CLAIM_INSUFFICIENT, CLAIM_NOT_EVALUABLE} or adm_status != "ADMITTED":
        research_action = RESEARCH_ACTION_HOLD
        rationale = (
            f"Admission status={adm_status}, claim_outcome={claim_outcome}: "
            "HOLD_FOR_EVIDENCE (BLOCKED or NOT_EVALUABLE paths cannot advance)."
        )
    else:
        raise GvV2B0BError(
            f"V2B0B_CLAIM_OUTCOME_NOT_AUTHORIZED_IN_B0B:{claim_outcome}"
        )

    if research_action in {RESEARCH_ACTION_ADVANCE, RESEARCH_ACTION_REJECT}:
        raise GvV2B0BError("V2B0B_NON_HOLD_RESEARCH_NOT_AUTHORIZED_IN_B0B")

    portfolio_action = PORTFOLIO_ACTION_NO_POSITION

    rationale_ref = f"{RATIONALE_REF_PREFIX}{claim['claim_evaluation_hash']}"
    if len(rationale_ref) > 128:
        raise GvV2B0BError("V2B0B_RATIONALE_REF_TOO_LONG")
    body = {
        "schema_version": RESEARCH_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "research_action": research_action,
        "portfolio_action": portfolio_action,
        "decision_id": DECISION_ID,
        "admission_hash": admission["admission_hash"],
        "admission_status": adm_status,
        "claim_evaluation_hash": claim["claim_evaluation_hash"],
        "claim_outcome": claim_outcome,
        "primary_block_reason": admission.get("primary_block_reason"),
        "rationale": rationale,
        "rationale_ref": rationale_ref,
        "slice_classification": SLICE_CLASSIFICATION,
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["research_decision_hash"] = domain_hash(RESEARCH_DOMAIN, body)
    return body


def v2b0b_rationale_ref(claim_evaluation_hash: str) -> str:
    digest = str(claim_evaluation_hash)
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise GvV2B0BError("V2B0B_CLAIM_HASH_INVALID")
    return f"{RATIONALE_REF_PREFIX}{digest}"


def build_v2b0b_decision(
    fixture_hash: str,
    fixture_id: str,
    *,
    rationale_ref: str,
) -> DecisionEnvelope:
    if not rationale_ref.startswith(RATIONALE_REF_PREFIX):
        raise GvV2B0BError("V2B0B_RATIONALE_REF_PREFIX_INVALID")
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id=DECISION_ID,
        action=PORTFOLIO_ACTION_NO_POSITION,
        requested_quantity=None,
        rationale_ref=rationale_ref,
    )


def build_v2b0b_book(*, research: Mapping[str, Any]) -> OpenBookBuild:
    rationale_ref = str(research["rationale_ref"])

    def decision_builder(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
        return build_v2b0b_decision(
            fixture_hash,
            fixture_id,
            rationale_ref=rationale_ref,
        )

    return _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )


def build_v2b0b_certified_result(
    research: Mapping[str, Any],
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    certified = build_certified_result_from_book(
        build_v2b0b_book(research=research),
        verifier_runner,
    )
    decision = certified.get("decision")
    if not isinstance(decision, Mapping):
        raise GvV2B0BError("V2B0B_DECISION_REQUIRED")
    if decision.get("decision_id") != DECISION_ID:
        raise GvV2B0BError("V2B0B_DECISION_ID_REQUIRED")
    if decision.get("action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvV2B0BError("V2B0B_PORTFOLIO_ACTION_REQUIRED")
    if decision.get("rationale_ref") != research.get("rationale_ref"):
        raise GvV2B0BError("V2B0B_RATIONALE_BINDING_INVALID")
    if certified.get("certification", {}).get("certification_status") != "CERTIFIED":
        raise GvV2B0BError("V2B0B_CERTIFIED_STATUS_REQUIRED")
    return certified


def build_decision_packet_markdown(
    *,
    access_authorization: Mapping[str, Any],
    package_manifest: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    claim: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> str:
    cert = certified.get("certification") or {}
    decision = certified.get("decision") or {}
    adm_cert = admission.get("admission_certificate") or {}
    lines = [
        "# GV-V2-B0B Decision Packet — MU G_supply Official Source Intake",
        "",
        f"- slice_classification: `{SLICE_CLASSIFICATION}`",
        f"- case_id: `{CASE_ID}`",
        f"- subject/module: `{SUBJECT}` / `{MODULE}`",
        f"- accession: `{ACCESSION}`",
        f"- source_family_id: `{SOURCE_FAMILY_ID}`",
        f"- independent_source_count: `1`",
        f"- access_authorization_hash: `{access_authorization['authorization_hash']}`",
        f"- authorization_recorded_at: `{access_authorization.get('authorization_recorded_at')}`",
        f"- retrieval_or_receipt_time (auth): `{access_authorization.get('retrieval_or_receipt_time')}`",
        f"- package_retrieved_at: `{package_manifest.get('retrieved_at')}`",
        f"- package_manifest_hash: `{package_manifest['package_manifest_hash']}`",
        f"- source_manifest_hash: `{source_manifest['source_manifest_hash']}`",
        f"- admission_hash: `{admission['admission_hash']}`",
        f"- admission_status: `{admission['status']}`",
        f"- admission_certificate_hash: `{adm_cert.get('admission_certificate_hash')}`",
        f"- claim_evaluation_hash: `{claim['claim_evaluation_hash']}`",
        f"- claim_outcome: `{claim.get('claim_outcome')}`",
        f"- research_action: `{research['research_action']}`",
        f"- portfolio_action: `{research['portfolio_action']}`",
        f"- decision_id: `{decision.get('decision_id')}`",
        f"- rationale_ref: `{decision.get('rationale_ref')}`",
        f"- certification_status: `{cert.get('certification_status')}`",
        f"- shipped_product_score: `39` (frozen; no uplift)",
        f"- functional_stage: `CERTIFIED_SINGLE_DECISION_OPERABLE`",
        f"- observed_comparison_count: `0`",
        "",
        "## Package objects (custody redundancy; one source)",
    ]
    for obj in package_manifest.get("objects") or []:
        lines.append(
            f"- `{obj['role']}` `{obj['filename']}` sha256=`{obj['sha256']}` "
            f"len={obj['byte_length']} retrieved_at=`{obj['retrieved_at']}`"
        )
    lines.extend(["", "## Admission checks"])
    for name, check in sorted((admission.get("checks") or {}).items()):
        if name == "contradictions":
            lines.append(
                f"- `{name}`: status=`{check.get('status')}` — {check.get('detail')}"
            )
        else:
            lines.append(
                f"- `{name}`: `{'PASS' if check.get('pass') else 'FAIL'}` — "
                f"{check.get('detail')}"
            )
    lines.extend(
        [
            "",
            "## Claim evaluation",
            f"- outcome: `{claim.get('claim_outcome')}`",
            f"- contradiction_status: `{claim.get('contradiction_status')}`",
            f"- statements: `{len(claim.get('statements') or [])}`",
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


def _exact_artifact_match(
    banked: Mapping[str, Any],
    rebuilt: Mapping[str, Any],
    *,
    error_code: str,
) -> None:
    """Exact canonical JSON equality — not mere hash self-consistency."""

    if _canonical_json_bytes(banked) != _canonical_json_bytes(rebuilt):
        raise GvV2B0BError(error_code)


def rebuild_canonical_b0b_chain(
    *,
    root: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
    include_result: bool = True,
) -> dict[str, Any]:
    """Deterministically rebuild B0B artifacts from pinned auth + raw SEC bytes.

    This is the sole derivation authority for verification. Banked artifacts are
    accepted only when they exact-match this rebuild.
    """

    base = Path(root) if root is not None else ROOT
    auth = load_access_authorization(root=base)
    package = build_package_manifest(root=base, access_authorization=auth)
    source = build_source_manifest(
        root=base, access_authorization=auth, package_manifest=package
    )
    admission = run_admission_checks(
        root=base,
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
    )
    claim = evaluate_g_supply_claim(
        root=base, admission=admission, package_manifest=package
    )
    research = build_g_supply_research_decision(admission, claim, root=base)
    out: dict[str, Any] = {
        "access_authorization": auth,
        "package_manifest": package,
        "source_manifest": source,
        "admission": admission,
        "claim": claim,
        "research": research,
    }
    if include_result:
        certified = build_v2b0b_certified_result(research, verifier_runner)
        result = build_result_document(
            access_authorization=auth,
            package_manifest=package,
            source_manifest=source,
            admission=admission,
            claim=claim,
            research=research,
            certified=certified,
        )
        out["certified"] = certified
        out["result"] = result
    return out


def verify_b0b_chain(
    *,
    root: Path | None = None,
    access_authorization: Mapping[str, Any],
    package_manifest: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    claim: Mapping[str, Any],
    research: Mapping[str, Any],
    result: Mapping[str, Any] | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> None:
    """B0B-R2: rebuild from pinned auth + raw SEC bytes; exact-compare banked.

    Hash self-consistency alone is insufficient: a rehashed false locator or a
    rehashed CLAIM_CONTRADICTED must fail. Canonical derivation is the rebuild.
    """

    base = Path(root) if root is not None else ROOT
    rebuilt = rebuild_canonical_b0b_chain(
        root=base,
        verifier_runner=verifier_runner,
        include_result=result is not None,
    )

    _exact_artifact_match(
        access_authorization,
        rebuilt["access_authorization"],
        error_code="V2B0B_AUTH_NOT_CANONICAL",
    )
    _exact_artifact_match(
        package_manifest,
        rebuilt["package_manifest"],
        error_code="V2B0B_PACKAGE_NOT_CANONICAL",
    )
    _exact_artifact_match(
        source_manifest,
        rebuilt["source_manifest"],
        error_code="V2B0B_SOURCE_NOT_CANONICAL",
    )
    _exact_artifact_match(
        admission,
        rebuilt["admission"],
        error_code="V2B0B_ADMISSION_NOT_CANONICAL",
    )
    _exact_artifact_match(
        claim,
        rebuilt["claim"],
        error_code="V2B0B_CLAIM_NOT_CANONICAL",
    )
    _exact_artifact_match(
        research,
        rebuilt["research"],
        error_code="V2B0B_RESEARCH_NOT_CANONICAL",
    )
    if result is not None:
        _exact_artifact_match(
            result,
            rebuilt["result"],
            error_code="V2B0B_RESULT_NOT_CANONICAL",
        )
    # Defense: B0B research surface must remain HOLD / NO_POSITION.
    if rebuilt["research"].get("research_action") != RESEARCH_ACTION_HOLD:
        raise GvV2B0BError("V2B0B_CANONICAL_RESEARCH_MUST_HOLD")
    if rebuilt["research"].get("portfolio_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvV2B0BError("V2B0B_CANONICAL_PORTFOLIO_MUST_NO_POSITION")
    if rebuilt["claim"].get("claim_outcome") != CLAIM_INSUFFICIENT:
        # Banked B0B ADMITTED package always evaluates insufficient in this slice.
        if rebuilt["admission"].get("status") == "ADMITTED":
            raise GvV2B0BError("V2B0B_CANONICAL_CLAIM_MUST_BE_INSUFFICIENT")


def load_verified_b0b_result(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    result_json_path: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Load banked B0B result only after rebuild-from-raw exact match succeeds."""

    base = Path(root) if root is not None else ROOT
    result_path = (
        Path(result_json_path)
        if result_json_path is not None
        else None
    )
    if case_dir is not None:
        out_dir = Path(case_dir)
    elif result_path is not None:
        out_dir = result_path.parent
    else:
        out_dir = base / "data" / "gv_v2_b0b" / "mu_0000723125-26-000015"
    if result_path is None:
        result_path = out_dir / "result.json"
    if not result_path.is_file() or result_path.is_symlink():
        raise GvV2B0BError("V2B0B_RESULT_MISSING")

    def _load(name: str, code: str) -> dict[str, Any]:
        path = _require_file(out_dir / name, code)
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise GvV2B0BError(f"{code}_NOT_OBJECT")
        return obj

    auth = _load("access_authorization.json", "V2B0B_ACCESS_AUTHORIZATION_MISSING")
    package = _load("package_manifest.json", "V2B0B_PACKAGE_MANIFEST_MISSING")
    source = _load("source_manifest.json", "V2B0B_SOURCE_MANIFEST_MISSING")
    admission = _load("admission_result.json", "V2B0B_ADMISSION_MISSING")
    claim = _load("claim_evaluation.json", "V2B0B_CLAIM_MISSING")
    research = _load("research_decision.json", "V2B0B_RESEARCH_MISSING")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise GvV2B0BError("V2B0B_RESULT_NOT_OBJECT")

    verify_b0b_chain(
        root=base,
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
        admission=admission,
        claim=claim,
        research=research,
        result=result,
        verifier_runner=verifier_runner,
    )
    return result


def build_result_document(
    *,
    access_authorization: Mapping[str, Any],
    package_manifest: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    claim: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
) -> dict[str, Any]:
    require_domain_hash(
        research,
        domain=RESEARCH_DOMAIN,
        hash_key="research_decision_hash",
        error_code="V2B0B_RESEARCH_DECISION_HASH_MISMATCH",
    )
    require_domain_hash(
        claim,
        domain=CLAIM_DOMAIN,
        hash_key="claim_evaluation_hash",
        error_code="V2B0B_CLAIM_EVALUATION_HASH_MISMATCH",
    )
    require_domain_hash(
        admission,
        domain=ADMISSION_DOMAIN,
        hash_key="admission_hash",
        error_code="V2B0B_ADMISSION_HASH_MISMATCH",
    )
    certificates = 1 if admission.get("status") == "ADMITTED" else 0
    body = {
        "schema_version": RESULT_SCHEMA,
        "case_id": CASE_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "slice_classification": SLICE_CLASSIFICATION,
        "accession": ACCESSION,
        "source_family_id": SOURCE_FAMILY_ID,
        "independent_source_count": 1,
        "access_authorization_hash": access_authorization["authorization_hash"],
        "package_manifest_hash": package_manifest["package_manifest_hash"],
        "source_manifest_hash": source_manifest["source_manifest_hash"],
        "admission_hash": admission["admission_hash"],
        "admission_status": admission["status"],
        "admission_certificate_hash": (
            (admission.get("admission_certificate") or {}).get(
                "admission_certificate_hash"
            )
        ),
        "primary_block_reason": admission.get("primary_block_reason"),
        "block_reasons": list(admission.get("block_reasons") or []),
        "claim_evaluation_hash": claim["claim_evaluation_hash"],
        "claim_outcome": claim.get("claim_outcome"),
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
        "real_external_source_packages_processed": 1,
        "data_admission_certificates_earned": certificates,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["result_hash"] = domain_hash(RESULT_DOMAIN, body)
    return body


def run_v2_b0b_official_source_intake(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    publish: bool = True,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Execute the full V2-B0B official-source vertical once; bank artifacts."""

    base = Path(root) if root is not None else ROOT
    out_dir = (
        Path(case_dir)
        if case_dir is not None
        else (base / "data" / "gv_v2_b0b" / "mu_0000723125-26-000015")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    auth = load_access_authorization(root=base)
    package = build_package_manifest(root=base, access_authorization=auth)
    source = build_source_manifest(
        root=base, access_authorization=auth, package_manifest=package
    )
    admission = run_admission_checks(
        root=base,
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
    )
    claim = evaluate_g_supply_claim(
        root=base, admission=admission, package_manifest=package
    )
    research = build_g_supply_research_decision(admission, claim, root=base)
    # B0B portfolio authority is always paper NO_POSITION; ADVANCE forbidden.
    if research.get("portfolio_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvV2B0BError("V2B0B_PORTFOLIO_ACTION_REQUIRED")
    if research.get("research_action") == RESEARCH_ACTION_ADVANCE:
        raise GvV2B0BError("V2B0B_ADVANCE_NOT_AUTHORIZED_IN_B0B")

    certified = build_v2b0b_certified_result(research, verifier_runner)
    result = build_result_document(
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
        admission=admission,
        claim=claim,
        research=research,
        certified=certified,
    )
    verify_b0b_chain(
        root=base,
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
        admission=admission,
        claim=claim,
        research=research,
        result=result,
    )
    packet_md = build_decision_packet_markdown(
        access_authorization=auth,
        package_manifest=package,
        source_manifest=source,
        admission=admission,
        claim=claim,
        research=research,
        certified=certified,
    )

    # Pre-read authorization must never be rewritten with package receipt.
    # If a banked auth exists in out_dir it must match the loaded root auth;
    # otherwise copy the verified pre-read object once for case banking.
    auth_path = out_dir / "access_authorization.json"
    if auth_path.is_file():
        existing_auth = json.loads(auth_path.read_text(encoding="utf-8"))
        if existing_auth.get("authorization_hash") != auth["authorization_hash"]:
            raise GvV2B0BError("V2B0B_AUTH_BANK_TAMPER")
        if existing_auth.get("retrieval_or_receipt_time") is not None:
            raise GvV2B0BError("V2B0B_AUTH_MUST_NOT_CONTAIN_RECEIPT_TIME")
    else:
        _atomic_write_json(auth_path, auth)

    _atomic_write_json(out_dir / "package_manifest.json", package)
    _atomic_write_json(out_dir / "source_manifest.json", source)
    _atomic_write_json(out_dir / "admission_result.json", admission)
    _atomic_write_json(out_dir / "claim_evaluation.json", claim)
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
        "accession": ACCESSION,
        "admission_status": admission["status"],
        "primary_block_reason": admission.get("primary_block_reason"),
        "block_reasons": list(admission.get("block_reasons") or []),
        "admission_hash": admission["admission_hash"],
        "claim_evaluation_hash": claim["claim_evaluation_hash"],
        "claim_outcome": claim.get("claim_outcome"),
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "decision_id": DECISION_ID,
        "rationale_ref": research["rationale_ref"],
        "certification_status": certified["certification"]["certification_status"],
        "certified_decision_result_hash": certified.get("certified_decision_result_hash"),
        "result_hash": result["result_hash"],
        "shipped_product_score": 39,
        "observed_comparison_count": 0,
        "real_external_source_packages_processed": 1,
        "data_admission_certificates_earned": result[
            "data_admission_certificates_earned"
        ],
        "published": publication is not None,
        "independent_source_count": 1,
    }


if __name__ == "__main__":
    out = run_v2_b0b_official_source_intake()
    print(json.dumps(out, indent=2, sort_keys=True))
