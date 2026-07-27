"""One-case evidence-gap triage machinery.

This module is intentionally pre-human and publication-free. It owns:
- positive source-file custody and deterministic answer-free projection;
- post-hosted-green candidate/session binding;
- one-shot arm state, equal maximum budgets, blinding, seals, and replay;
- provider-neutral OpenSSH SSHSIG identity and detached-attestation validation;
- sign-independent eligibility and the frozen IMPROVED/NOT_IMPROVED rule.

It never mutates current product authority, score, stage, or observed count.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
from typing import Any

from core.gv_fs0_canonical import (
    CANONICAL_TIMESTAMP_RE,
    SHA256_RE,
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
    sha256_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_DIR = ROOT / "data" / "gv_one_case_delta" / "case_1"
DEFAULT_BINDING_PATH = DEFAULT_CASE_DIR / "experiment_binding.json"
DEFAULT_BUNDLE_PATH = DEFAULT_CASE_DIR / "admissible_evidence_bundle.json"
DEFAULT_PROJECTION_PATH = DEFAULT_CASE_DIR / "answer_free_projection.json"
DEFAULT_PROJECTION_MANIFEST_PATH = DEFAULT_CASE_DIR / "projection_manifest.json"

OBSERVATION_CLASS = "EVIDENCE_GAP_TRIAGE_ONLY"
CASE_ID = "V2_ALPHA0_MU_G_SUPPLY_CLOSE_1"
SUBJECT_CASE = "MU_G_SUPPLY"
MODULE = "G_supply"
CUTOFF_AT = "2026-07-23T00:00:00.000000Z"
MAXIMUM_BUDGET_SECONDS = 60 * 60
GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")

SCHEMA_BINDING = "gv_one_case_delta_experiment_binding_v1"
SCHEMA_BUNDLE = "gv_one_case_delta_admissible_evidence_v1"
SCHEMA_PROJECTION = "gv_one_case_delta_answer_free_projection_v1"
SCHEMA_PROJECTION_MANIFEST = "gv_one_case_delta_projection_manifest_v1"
SCHEMA_HOSTED_PROOF = "gv_one_case_delta_hosted_proof_v1"
SCHEMA_SESSION_MANIFEST = "gv_one_case_delta_session_manifest_v1"
SCHEMA_SESSION_STATE = "gv_one_case_delta_session_state_v1"
SCHEMA_IDENTITY = "gv_one_case_delta_identity_evidence_v1"
SCHEMA_ATTESTATION = "gv_one_case_delta_session_attestation_v1"
SCHEMA_REVIEW_PACKAGE = "gv_one_case_delta_review_package_v1"
SCHEMA_REVIEW_MAPPING = "gv_one_case_delta_review_mapping_v1"
SCHEMA_RESULT = "gv_one_case_delta_result_v1"

DOMAIN_BINDING = "GV-ONE-CASE-DELTA:BINDING:V1"
DOMAIN_BUNDLE = "GV-ONE-CASE-DELTA:EVIDENCE:V1"
DOMAIN_PROJECTION = "GV-ONE-CASE-DELTA:PROJECTION:V1"
DOMAIN_PROJECTION_SCHEMA = "GV-ONE-CASE-DELTA:PROJECTION-SCHEMA:V1"
DOMAIN_PROJECTION_MANIFEST = "GV-ONE-CASE-DELTA:PROJECTION-MANIFEST:V1"
DOMAIN_HOSTED_PROOF = "GV-ONE-CASE-DELTA:HOSTED-PROOF:V1"
DOMAIN_SESSION_MANIFEST = "GV-ONE-CASE-DELTA:SESSION-MANIFEST:V1"
DOMAIN_EVENT = "GV-ONE-CASE-DELTA:EVENT:V1"
DOMAIN_STATE = "GV-ONE-CASE-DELTA:STATE:V1"
DOMAIN_IDENTITY = "GV-ONE-CASE-DELTA:IDENTITY:V1"
DOMAIN_ATTESTATION = "GV-ONE-CASE-DELTA:ATTESTATION:V1"
DOMAIN_REVIEW_PACKAGE = "GV-ONE-CASE-DELTA:REVIEW-PACKAGE:V1"
DOMAIN_REVIEW_MAPPING = "GV-ONE-CASE-DELTA:REVIEW-MAPPING:V1"
DOMAIN_RUBRIC = "GV-ONE-CASE-DELTA:RUBRIC:V1"
DOMAIN_RESULT = "GV-ONE-CASE-DELTA:RESULT:V1"

PROJECTION_SCHEMA_HASH = domain_hash(
    DOMAIN_PROJECTION_SCHEMA, {"schema_version": SCHEMA_PROJECTION}
)

IDENTITY_ADAPTER = "OPENSSH_SSHSIG_V1"
IDENTITY_NAMESPACE = "gv-one-case-human-identity-v1"
ROLE_NAMESPACE = "gv-one-case-role-v1"
ATTESTATION_NAMESPACE = "gv-one-case-session-attestation-v1"
HOSTED_PROOF_NAMESPACE = "gv-one-case-hosted-proof-v1"
IDENTITY_VERIFICATION_LEVEL = "IN_PERSON_OR_LIVE_VIDEO_GOVERNMENT_ID_MATCH"

ROLE_OPERATOR = "OPERATOR"
ROLE_REVIEWER = "REVIEWER"
PHASE_PRE_EXPOSURE = "PRE_EXPOSURE"
PHASE_PRE_EXPOSURE_ABORTED = "PRE_EXPOSURE_ABORTED"
PHASE_BASELINE_OPEN = "BASELINE_OPEN"
PHASE_BASELINE_SEALED = "BASELINE_SEALED"
PHASE_PROJECTION_RELEASED = "PROJECTION_RELEASED"
PHASE_POST_OPEN = "POST_OPEN"
PHASE_POST_SEALED = "POST_SEALED"
PHASE_REVIEW_PACKAGE_SEALED = "REVIEW_PACKAGE_SEALED"
PHASE_REVIEW_AUTHORITY_SEALED = "REVIEW_AUTHORITY_SEALED"
PHASE_TERMINAL_ELIGIBLE = "TERMINAL_ELIGIBLE"
PHASE_TERMINAL_INELIGIBLE = "TERMINAL_INELIGIBLE"

RESEARCH_ACTIONS = frozenset(
    {"ADVANCE_TO_FULL_RESEARCH", "HOLD_FOR_EVIDENCE", "REJECT_THESIS"}
)
RUBRIC_ITEMS = (
    "selected_action_defensibility",
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
    "supply_demand_business_shareholder_valuation_claim_separation",
    "avoidance_of_claims_beyond_evidence",
    "rationale_traceability",
)
TARGETED_DIMENSIONS = (
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
)
CORE_SAFETY_DIMENSIONS = (
    "selected_action_defensibility",
    "avoidance_of_claims_beyond_evidence",
)

ALLOWED_INPUT_HASHES: dict[str, str] = {
    "data/gv_v2_alpha0/case_mu_g_supply_close_1/case_manifest.json": "70e79d92c806249f06c1bc844f5ba21d6128631bd2e95a02cdc675402ae6fa27",
    "data/gv_v2_alpha0/case_mu_g_supply_close_1/coverage.json": "4f37abda3aa59d70173da9ece0b07595fec11e0ce33eeeaf2f8c9e0b49b3231b",
    "data/gv_v2_alpha0/case_mu_g_supply_close_1/evidence_panel.json": "9849343a665211d0c4cde52c217577075c0a5eb9d3805e53dab9b95d140b70bf",
    "data/gv_v2_b0b/mu_0000723125-26-000015/package_manifest.json": "601465e9682751532b7d90083099de4de2710ea0920b90a3e3c1d5b25ccc8459",
    "data/gv_v2_b0b/mu_0000723125-26-000015/source_manifest.json": "3fad632bd4153a3005bb3b1a68547d49c6435438d1c42e7e7b9ba99ae5bfe778",
    "data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm": "bf4c3fb1833243d1c41c0426c4e0332d3a2f61a2b44e534fe8ff13648f205e20",
    "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/package_manifest.json": "43adcb4e45cb5dbc3e1e44e7663e81bcf48dd31d946f66cf6286ccaf25775028",
    "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/fact_set.json": "619cffd785ae8a97d6bb45406660ce4f23f5e4d3a6cf4f3dcb3bce1265b94a62",
    "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/nvda-20260426.htm": "1b5de37b973da4a3f1cd31a09aa455c01c519ea7cc409c73de2250ad156f99e4",
}

FORBIDDEN_SOURCE_PATHS = frozenset(
    {
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/adjudication.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/case_claim.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/case_workspace_view.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/certified_decision_result.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/decision_packet.md",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/export_bundle.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/operator_confirmation.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/pre_adjudication_seal.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/research_decision.json",
        "data/gv_v2_alpha0/case_mu_g_supply_close_1/result.json",
        "data/gv_v2_b0b/mu_0000723125-26-000015/claim_evaluation.json",
        "data/gv_v2_b0b/mu_0000723125-26-000015/decision_packet.md",
        "data/gv_v2_b0b/mu_0000723125-26-000015/research_decision.json",
        "data/gv_v2_b0b/mu_0000723125-26-000015/result.json",
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/decision_packet.md",
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/operator_decision_capture.json",
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/research_decision.json",
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/result.json",
    }
)

FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        "adjudication",
        "operator_confirmation",
        "research_decision",
        "certified_decision_result",
        "portfolio_action",
        "decision_id",
        "certification_id",
        "portfolio_book_id",
        "receipt_id",
        "operator_id",
        "selected_portfolio_action",
        "shipped_product_score",
        "functional_stage",
        "observed_comparison_count",
        "dogfood_status",
    }
)
FORBIDDEN_OUTPUT_FRAGMENTS = (
    "DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1",
    "889cc831fe405e5aad1f13225f06fe666036390defeff6652b39d0d656225376",
    "NO_POSITION",
    "ALPHA0:CLOSE:",
    "CERTIFIED_MULTI_SOURCE_CASE_OPERABLE",
)
REVIEW_FORBIDDEN_KEYS = frozenset(
    {
        "arm",
        "baseline",
        "post",
        "godview",
        "projection_hash",
        "bundle_hash",
        "session_nonce",
        "session_manifest_hash",
        "event_hash",
        "elapsed_seconds",
        "started_at",
        "ended_at",
        "schema_version",
        "file_path",
        "case_id",
        "decision_id",
        "receipt_id",
        "portfolio_action",
    }
)

Submission = Mapping[str, Any]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class OneCaseDeltaError(RuntimeError):
    """Fail-closed protocol error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise OneCaseDeltaError(code)


def _hash(domain: str, body: Mapping[str, Any]) -> str:
    return domain_hash(domain, dict(body))


def _with_hash(domain: str, body: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(body)
    result[field] = _hash(domain, body)
    return result


def _without_hash(record: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != field}


def _validate_embedded_hash(
    record: Mapping[str, Any], *, domain: str, field: str, code: str
) -> None:
    actual = record.get(field)
    _require(isinstance(actual, str) and SHA256_RE.fullmatch(actual) is not None, code)
    _require(_hash(domain, _without_hash(record, field)) == actual, code)


def _parse_timestamp(value: str) -> datetime:
    _require(isinstance(value, str) and CANONICAL_TIMESTAMP_RE.fullmatch(value) is not None, "TIMESTAMP_INVALID")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def canonical_timestamp(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    _require(value.tzinfo is not None, "TIMESTAMP_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _is_junction(path: Path) -> bool:
    checker = getattr(os.path, "isjunction", None)
    return bool(checker and checker(path))


def _relative_parts(root: Path, target: Path) -> tuple[Path, ...]:
    relative = target.relative_to(root)
    current = root
    parts: list[Path] = []
    for part in relative.parts:
        current = current / part
        parts.append(current)
    return tuple(parts)


def _validate_source_path(repo_root: Path, relative_path: str) -> Path:
    _require(relative_path in ALLOWED_INPUT_HASHES, "SOURCE_PATH_NOT_ALLOWLISTED")
    raw = Path(relative_path)
    _require(not raw.is_absolute() and ".." not in raw.parts, "SOURCE_PATH_INVALID")
    root = repo_root.resolve(strict=True)
    lexical = repo_root / raw
    for component in _relative_parts(repo_root, lexical):
        _require(not component.is_symlink(), "SOURCE_SYMLINK_PROHIBITED")
        _require(not _is_junction(component), "SOURCE_JUNCTION_PROHIBITED")
    resolved = lexical.resolve(strict=True)
    _require(resolved.is_relative_to(root), "SOURCE_OUTSIDE_REPOSITORY")
    _require(resolved.is_file(), "SOURCE_FILE_REQUIRED")
    stat = resolved.stat()
    _require(getattr(stat, "st_nlink", 1) == 1, "SOURCE_HARDLINK_PROHIBITED")
    for forbidden in FORBIDDEN_SOURCE_PATHS:
        forbidden_path = repo_root / forbidden
        if forbidden_path.exists():
            try:
                _require(not os.path.samefile(resolved, forbidden_path), "SOURCE_ALIASES_FORBIDDEN_PATH")
            except OSError as exc:
                raise OneCaseDeltaError("SOURCE_ALIAS_CHECK_FAILED") from exc
    return resolved


class AllowlistedSourceReader:
    """Read only exact path/hash-bound source inputs and retain the read set."""

    def __init__(self, repo_root: Path, expected: Mapping[str, str]) -> None:
        self.repo_root = repo_root
        self.expected = dict(expected)
        _require(self.expected == ALLOWED_INPUT_HASHES, "SOURCE_ALLOWLIST_MISMATCH")
        self.read_set: list[dict[str, str]] = []

    def read_bytes(self, relative_path: str) -> bytes:
        _require(relative_path not in {item["path"] for item in self.read_set}, "SOURCE_READ_DUPLICATED")
        path = _validate_source_path(self.repo_root, relative_path)
        raw = path.read_bytes()
        actual_hash = sha256_bytes(raw)
        _require(actual_hash == self.expected[relative_path], "SOURCE_HASH_MISMATCH")
        self.read_set.append({"path": relative_path, "sha256": actual_hash})
        return raw

    def read_json(self, relative_path: str) -> dict[str, Any]:
        parsed = parse_canonical_document_bytes(self.read_bytes(relative_path))
        _require(isinstance(parsed, dict), "SOURCE_JSON_OBJECT_REQUIRED")
        return parsed

    def assert_complete(self) -> None:
        _require(
            {item["path"] for item in self.read_set} == set(self.expected),
            "SOURCE_ALLOWLIST_NOT_FULLY_READ",
        )


def load_experiment_binding(path: Path = DEFAULT_BINDING_PATH) -> dict[str, Any]:
    parsed = parse_canonical_document_bytes(path.read_bytes())
    _require(isinstance(parsed, dict), "BINDING_OBJECT_REQUIRED")
    _validate_embedded_hash(parsed, domain=DOMAIN_BINDING, field="experiment_binding_hash", code="BINDING_HASH_INVALID")
    _require(parsed.get("schema_version") == SCHEMA_BINDING, "BINDING_SCHEMA_INVALID")
    _require(parsed.get("observation_class") == OBSERVATION_CLASS, "BINDING_OBSERVATION_CLASS_INVALID")
    _require(parsed.get("case_id") == CASE_ID, "BINDING_CASE_INVALID")
    _require(parsed.get("cutoff_at") == CUTOFF_AT, "BINDING_CUTOFF_INVALID")
    _require(parsed.get("maximum_budget_seconds_per_arm") == MAXIMUM_BUDGET_SECONDS, "BINDING_BUDGET_INVALID")
    _require(parsed.get("early_submission_allowed") is True, "BINDING_EARLY_SUBMISSION_INVALID")
    _require(parsed.get("latency_endpoint") == "NONE", "BINDING_LATENCY_INVALID")
    _require(parsed.get("identity_adapter") == IDENTITY_ADAPTER, "BINDING_IDENTITY_ADAPTER_INVALID")
    _require(parsed.get("allowed_input_files") == ALLOWED_INPUT_HASHES, "BINDING_ALLOWLIST_INVALID")
    _require("candidate_sha" not in parsed and "candidate_tree" not in parsed, "BINDING_SELF_REFERENCE_PROHIBITED")
    return parsed


def _verify_excerpt(raw: bytes, evidence: Mapping[str, Any]) -> None:
    start = evidence.get("byte_start")
    end = evidence.get("byte_end")
    excerpt = evidence.get("exact_excerpt")
    _require(isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(raw), "EXCERPT_RANGE_INVALID")
    _require(isinstance(excerpt, str), "EXCERPT_TEXT_REQUIRED")
    actual = raw[start:end]
    _require(actual.decode("utf-8") == excerpt, "EXCERPT_BYTES_MISMATCH")
    _require(sha256_bytes(actual) == evidence.get("exact_excerpt_hash"), "EXCERPT_HASH_MISMATCH")


def _scan_forbidden(value: Any, *, review: bool = False, path: str = "$" ) -> None:
    forbidden_keys = REVIEW_FORBIDDEN_KEYS if review else FORBIDDEN_OUTPUT_KEYS
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require(key not in forbidden_keys, f"FORBIDDEN_KEY:{path}.{key}")
            _scan_forbidden(item, review=review, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_forbidden(item, review=review, path=f"{path}[{index}]")
    elif isinstance(value, str):
        for fragment in FORBIDDEN_OUTPUT_FRAGMENTS:
            _require(fragment not in value, f"FORBIDDEN_VALUE:{path}")
        if review:
            normalized = value.replace("\\", "/")
            _require("data/" not in normalized and "docs/" not in normalized, f"REVIEW_PATH_LEAK:{path}")
            for fragment in ("BASELINE", "POST", "GODVIEW", "ALPHA", "PACKET"):
                _require(fragment not in value.upper(), f"REVIEW_ORIGIN_LEAK:{path}")


def _artifact_body(
    *, reader: AllowlistedSourceReader, binding: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_manifest = reader.read_json("data/gv_v2_alpha0/case_mu_g_supply_close_1/case_manifest.json")
    coverage = reader.read_json("data/gv_v2_alpha0/case_mu_g_supply_close_1/coverage.json")
    panel = reader.read_json("data/gv_v2_alpha0/case_mu_g_supply_close_1/evidence_panel.json")
    mu_package = reader.read_json("data/gv_v2_b0b/mu_0000723125-26-000015/package_manifest.json")
    mu_source = reader.read_json("data/gv_v2_b0b/mu_0000723125-26-000015/source_manifest.json")
    mu_raw = reader.read_bytes("data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm")
    nv_package = reader.read_json("data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/package_manifest.json")
    nv_facts = reader.read_json("data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/fact_set.json")
    nv_raw = reader.read_bytes("data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/nvda-20260426.htm")
    reader.assert_complete()

    _require(case_manifest.get("case_id") == CASE_ID, "CASE_MANIFEST_ID_INVALID")
    _require(coverage.get("coverage_status") == "PARTIAL", "COVERAGE_STATUS_INVALID")
    _require(panel.get("coverage_status") == "PARTIAL", "EVIDENCE_PANEL_STATUS_INVALID")
    _require(panel.get("overlap_count") == 1, "EVIDENCE_PANEL_OVERLAP_INVALID")
    overlap = panel["overlap_panels"][0]
    family_one = overlap["family_one"]
    family_two = overlap["family_two"]
    _verify_excerpt(mu_raw, family_one)
    _verify_excerpt(nv_raw, family_two)

    neutral_evidence = [
        {
            "source_locator_id": "SRC_MU_001",
            "source_family_id": family_one["source_family_id"],
            "official_locator": family_one["official_locator"],
            "section_or_element_locator": family_one["section_or_element_locator"],
            "exact_excerpt": family_one["exact_excerpt"],
            "exact_excerpt_hash": family_one["exact_excerpt_hash"],
            "source_object_hash": family_one["source_object_hash"],
        },
        {
            "source_locator_id": "SRC_NVDA_001",
            "source_family_id": family_two["source_family_id"],
            "official_locator": family_two["official_locator"],
            "section_or_element_locator": family_two["section_or_element_locator"],
            "exact_excerpt": family_two["exact_excerpt"],
            "exact_excerpt_hash": family_two["exact_excerpt_hash"],
            "source_object_hash": family_two["source_object_hash"],
        },
    ]

    bundle_body = {
        "schema_version": SCHEMA_BUNDLE,
        "observation_class": OBSERVATION_CLASS,
        "case_id": CASE_ID,
        "subject_case": SUBJECT_CASE,
        "module": MODULE,
        "cutoff_at": CUTOFF_AT,
        "maximum_budget_seconds_per_arm": MAXIMUM_BUDGET_SECONDS,
        "early_submission_allowed": True,
        "latency_endpoint": "NONE",
        "research_action_set": sorted(RESEARCH_ACTIONS),
        "neutral_source_locator_ids": [item["source_locator_id"] for item in neutral_evidence],
        "admissible_evidence": neutral_evidence,
        "source_package_custody": {
            "family_one_package_manifest_hash": binding["family_one_package_manifest_hash"],
            "family_two_package_manifest_hash": binding["family_two_package_manifest_hash"],
            "family_one_manifest_schema": mu_package.get("schema_version"),
            "family_one_source_schema": mu_source.get("schema_version"),
            "family_two_manifest_schema": nv_package.get("schema_version"),
            "family_two_fact_schema": nv_facts.get("schema_version"),
        },
    }

    projection_body = {
        "schema_version": SCHEMA_PROJECTION,
        "observation_class": OBSERVATION_CLASS,
        "case_id": CASE_ID,
        "coverage": {
            "status": "PARTIAL",
            "meaning": "Evidence overlap only; not claim sufficiency or investment authority.",
            "overlap": [
                {
                    "overlap_class": overlap["overlap_class"],
                    "note": overlap["note"],
                    "source_locator_ids": ["SRC_MU_001", "SRC_NVDA_001"],
                }
            ],
            "non_overlap_notes": list(panel["non_overlap_notes"]),
        },
        "claim_state": "CLAIM_INSUFFICIENT",
        "dimension_states": {
            "physical_supply_telemetry": "FAIL",
            "industry_economics": "NOT_EVALUATED",
            "business_capture": "NOT_EVALUATED",
            "shareholder_capture": "NOT_EVALUATED",
            "decision_time_price_envelope": "NOT_EVALUATED",
        },
        "missing_indispensable_evidence": [
            "Physical supply telemetry tied to Micron-relevant supply conditions.",
            "Evidence translating industry conditions into Micron business capture.",
            "Evidence translating business capture into shareholder cash-flow capture.",
            "Decision-time price-envelope evidence for expectations consistency.",
            "Economics sufficient to connect the evidence chain to an investment decision.",
        ],
        "contradictions_and_falsifiers": [
            "Peer/customer memory-price language does not independently corroborate Micron physical supply.",
            "Issuer constrained-supply language without physical telemetry cannot identify physical supply condition.",
            "Facility or expansion disclosures without paired independent evidence do not establish business capture.",
            "Any claim of shareholder or valuation capture is falsified by the absence of those evaluated dimensions.",
        ],
        "claim_separation": {
            "supply": "Language indicates constrained supply context; physical telemetry is absent.",
            "demand": "Industry-context demand language is not a complete demand model.",
            "business_capture": "Not evaluated.",
            "shareholder_capture": "Not evaluated.",
            "valuation": "Not evaluated against the decision-time price envelope.",
        },
        "admissible_source_locator_ids": ["SRC_MU_001", "SRC_NVDA_001"],
    }
    _scan_forbidden(projection_body)
    return bundle_body, projection_body


def build_pre_human_artifacts(
    repo_root: Path = ROOT, binding_path: Path = DEFAULT_BINDING_PATH
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    binding = load_experiment_binding(binding_path)
    reader = AllowlistedSourceReader(repo_root, binding["allowed_input_files"])
    bundle_body, projection_body = _artifact_body(reader=reader, binding=binding)
    bundle = _with_hash(DOMAIN_BUNDLE, bundle_body, "evidence_bundle_hash")
    projection = _with_hash(DOMAIN_PROJECTION, projection_body, "projection_hash")
    manifest_body = {
        "schema_version": SCHEMA_PROJECTION_MANIFEST,
        "experiment_binding_hash": binding["experiment_binding_hash"],
        "evidence_bundle_hash": bundle["evidence_bundle_hash"],
        "projection_hash": projection["projection_hash"],
        "projection_schema": SCHEMA_PROJECTION,
        "source_read_set": reader.read_set,
        "source_read_set_complete": True,
        "forbidden_source_paths": sorted(FORBIDDEN_SOURCE_PATHS),
        "publication_authority": False,
        "human_result_present": False,
    }
    manifest = _with_hash(DOMAIN_PROJECTION_MANIFEST, manifest_body, "projection_manifest_hash")
    return bundle, projection, manifest


def assert_tracked_pre_human_artifacts(
    repo_root: Path = ROOT, binding_path: Path = DEFAULT_BINDING_PATH
) -> None:
    expected = build_pre_human_artifacts(repo_root, binding_path)
    paths = (DEFAULT_BUNDLE_PATH, DEFAULT_PROJECTION_PATH, DEFAULT_PROJECTION_MANIFEST_PATH)
    for path, record in zip(paths, expected, strict=True):
        _require(path.read_bytes() == canonical_document_bytes(record), f"TRACKED_ARTIFACT_DRIFT:{path.name}")


def verify_hosted_proof(
    record: Mapping[str, Any],
    *,
    candidate_sha: str,
    candidate_tree: str,
    trusted_proof_issuers: Mapping[str, str],
    runner: CommandRunner = subprocess.run,
) -> str:
    _require(record.get("schema_version") == SCHEMA_HOSTED_PROOF, "HOSTED_PROOF_SCHEMA_INVALID")
    _require(record.get("adapter") == IDENTITY_ADAPTER, "HOSTED_PROOF_ADAPTER_INVALID")
    provider = record.get("proof_provider")
    _require(
        isinstance(provider, str) and provider in trusted_proof_issuers,
        "HOSTED_PROOF_PROVIDER_UNTRUSTED",
    )
    provider_key = trusted_proof_issuers[provider]
    _require(record.get("provider_public_key") == provider_key, "HOSTED_PROOF_PROVIDER_KEY_MISMATCH")
    payload = record.get("payload")
    _require(isinstance(payload, Mapping), "HOSTED_PROOF_PAYLOAD_REQUIRED")
    _require(payload.get("candidate_sha") == candidate_sha, "HOSTED_PROOF_CANDIDATE_MISMATCH")
    _require(payload.get("candidate_tree") == candidate_tree, "HOSTED_PROOF_TREE_MISMATCH")
    _require(payload.get("workflow_name") == "GV-FS0 Product", "HOSTED_PROOF_WORKFLOW_INVALID")
    _require(payload.get("windows_conclusion") == "SUCCESS", "HOSTED_WINDOWS_NOT_GREEN")
    _require(payload.get("linux_conclusion") == "SUCCESS", "HOSTED_LINUX_NOT_GREEN")
    for field in ("proof_id", "windows_run_id", "linux_run_id"):
        _require(isinstance(payload.get(field), str) and payload[field].strip(), f"HOSTED_PROOF_FIELD_REQUIRED:{field}")
    _parse_timestamp(payload.get("verified_at"))
    _verify_sshsig(
        public_key=provider_key,
        identity=provider,
        namespace=HOSTED_PROOF_NAMESPACE,
        signature=record.get("signature", ""),
        message=canonical_document_bytes(dict(payload)),
        runner=runner,
    )
    body = dict(record)
    body.pop("hosted_proof_hash", None)
    digest = _hash(DOMAIN_HOSTED_PROOF, body)
    stored = record.get("hosted_proof_hash")
    if stored is not None:
        _require(stored == digest, "HOSTED_PROOF_HASH_INVALID")
    return digest


def create_session_manifest(
    *,
    candidate_sha: str,
    candidate_tree: str,
    experiment_binding_hash: str,
    evidence_bundle_hash: str,
    projection_hash: str,
    projection_manifest_hash: str,
    projection_schema_hash: str,
    operator_instruction_hash: str,
    reviewer_instruction_hash: str,
    hosted_proof_identity: Mapping[str, Any],
    trusted_proof_issuers: Mapping[str, str],
    session_nonce: str | None = None,
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    for value, code in ((candidate_sha, "CANDIDATE_SHA_INVALID"), (candidate_tree, "CANDIDATE_TREE_INVALID")):
        _require(isinstance(value, str) and GIT_OID_RE.fullmatch(value) is not None, code)
    for value, code in (
        (experiment_binding_hash, "EXPERIMENT_BINDING_HASH_INVALID"),
        (evidence_bundle_hash, "EVIDENCE_BUNDLE_HASH_INVALID"),
        (projection_hash, "PROJECTION_HASH_INVALID"),
        (projection_manifest_hash, "PROJECTION_MANIFEST_HASH_INVALID"),
        (projection_schema_hash, "PROJECTION_SCHEMA_HASH_INVALID"),
        (operator_instruction_hash, "OPERATOR_INSTRUCTION_HASH_INVALID"),
        (reviewer_instruction_hash, "REVIEWER_INSTRUCTION_HASH_INVALID"),
    ):
        _require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, code)
    _require(projection_schema_hash == PROJECTION_SCHEMA_HASH, "PROJECTION_SCHEMA_HASH_MISMATCH")
    hosted_proof_hash = verify_hosted_proof(
        hosted_proof_identity,
        candidate_sha=candidate_sha,
        candidate_tree=candidate_tree,
        trusted_proof_issuers=trusted_proof_issuers,
        runner=runner,
    )
    nonce = session_nonce or secrets.token_hex(32)
    _require(len(nonce) >= 32, "SESSION_NONCE_TOO_SHORT")
    body = {
        "schema_version": SCHEMA_SESSION_MANIFEST,
        "candidate_sha": candidate_sha,
        "candidate_tree": candidate_tree,
        "experiment_binding_hash": experiment_binding_hash,
        "evidence_bundle_hash": evidence_bundle_hash,
        "projection_hash": projection_hash,
        "projection_manifest_hash": projection_manifest_hash,
        "projection_schema_hash": projection_schema_hash,
        "operator_instruction_hash": operator_instruction_hash,
        "reviewer_instruction_hash": reviewer_instruction_hash,
        "hosted_proof_identity": dict(hosted_proof_identity),
        "hosted_proof_hash": hosted_proof_hash,
        "session_nonce": nonce,
        "one_shot_state": "AVAILABLE_PRE_EXPOSURE",
    }
    return _with_hash(DOMAIN_SESSION_MANIFEST, body, "session_manifest_hash")


def create_session_state(
    session_manifest: Mapping[str, Any],
    *,
    trusted_proof_issuers: Mapping[str, str],
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    _validate_embedded_hash(
        session_manifest,
        domain=DOMAIN_SESSION_MANIFEST,
        field="session_manifest_hash",
        code="SESSION_MANIFEST_HASH_INVALID",
    )
    proof_hash = verify_hosted_proof(
        session_manifest["hosted_proof_identity"],
        candidate_sha=session_manifest["candidate_sha"],
        candidate_tree=session_manifest["candidate_tree"],
        trusted_proof_issuers=trusted_proof_issuers,
        runner=runner,
    )
    _require(proof_hash == session_manifest.get("hosted_proof_hash"), "SESSION_HOSTED_PROOF_HASH_MISMATCH")
    _require(
        session_manifest.get("projection_schema_hash") == PROJECTION_SCHEMA_HASH,
        "SESSION_PROJECTION_SCHEMA_HASH_MISMATCH",
    )
    body = {
        "schema_version": SCHEMA_SESSION_STATE,
        "session_manifest_hash": session_manifest["session_manifest_hash"],
        "session_nonce": session_manifest["session_nonce"],
        "bound_evidence_bundle_hash": session_manifest["evidence_bundle_hash"],
        "bound_projection_hash": session_manifest["projection_hash"],
        "bound_projection_manifest_hash": session_manifest["projection_manifest_hash"],
        "phase": PHASE_PRE_EXPOSURE,
        "one_shot_consumed": False,
        "events": [],
    }
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def verify_event_chain(state: Mapping[str, Any]) -> None:
    _validate_embedded_hash(state, domain=DOMAIN_STATE, field="session_state_hash", code="SESSION_STATE_HASH_INVALID")
    previous = "0" * 64
    for sequence, event in enumerate(state.get("events", []), start=1):
        _require(event.get("sequence") == sequence, "EVENT_SEQUENCE_INVALID")
        _require(event.get("previous_event_hash") == previous, "EVENT_CHAIN_PREVIOUS_INVALID")
        _validate_embedded_hash(event, domain=DOMAIN_EVENT, field="event_hash", code="EVENT_HASH_INVALID")
        previous = event["event_hash"]


def _append_event(
    state: Mapping[str, Any], *, event_type: str, payload: Mapping[str, Any], occurred_at: str
) -> dict[str, Any]:
    verify_event_chain(state)
    events = list(state["events"])
    previous = events[-1]["event_hash"] if events else "0" * 64
    event_body = {
        "sequence": len(events) + 1,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "previous_event_hash": previous,
        "payload": dict(payload),
    }
    events.append(_with_hash(DOMAIN_EVENT, event_body, "event_hash"))
    body = _without_hash(state, "session_state_hash")
    body["events"] = events
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def pre_exposure_abort(state: Mapping[str, Any], *, reason: str, occurred_at: str) -> dict[str, Any]:
    _require(state.get("phase") == PHASE_PRE_EXPOSURE, "PRE_EXPOSURE_ABORT_TOO_LATE")
    _require(state.get("one_shot_consumed") is False, "ONESHOT_ALREADY_CONSUMED")
    result = _append_event(state, event_type="PRE_EXPOSURE_ABORT", payload={"reason": reason}, occurred_at=occurred_at)
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_PRE_EXPOSURE_ABORTED
    body["one_shot_consumed"] = False
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def _validate_operator_eligibility(attestation: Mapping[str, Any]) -> None:
    required = (
        "no_prior_alpha_claim_exposure",
        "no_alpha_implementation_dogfood_audit_or_review",
        "no_material_post_cutoff_information",
        "no_current_price_or_subsequent_event_use",
        "no_outside_research",
        "no_projection_access_before_baseline_seal",
    )
    _require(all(attestation.get(item) is True for item in required), "OPERATOR_ELIGIBILITY_INVALID")


def open_baseline(
    state: Mapping[str, Any],
    *,
    session_manifest: Mapping[str, Any],
    operator_identity_evidence: Mapping[str, Any],
    trusted_issuers: Mapping[str, str],
    eligibility: Mapping[str, Any],
    occurred_at: str,
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    _require(state.get("phase") == PHASE_PRE_EXPOSURE, "BASELINE_OPEN_PHASE_INVALID")
    _require(state.get("one_shot_consumed") is False, "ONESHOT_ALREADY_CONSUMED")
    _validate_embedded_hash(
        session_manifest,
        domain=DOMAIN_SESSION_MANIFEST,
        field="session_manifest_hash",
        code="SESSION_MANIFEST_HASH_INVALID",
    )
    _require(
        state.get("session_manifest_hash") == session_manifest.get("session_manifest_hash"),
        "BASELINE_SESSION_MISMATCH",
    )
    operator_identity_evidence_hash = verify_identity_evidence(
        operator_identity_evidence,
        expected_role=ROLE_OPERATOR,
        session_manifest=session_manifest,
        trusted_issuers=trusted_issuers,
        runner=runner,
    )
    _validate_operator_eligibility(eligibility)
    result = _append_event(
        state,
        event_type="BASELINE_OPEN",
        payload={
            "operator_identity_evidence_hash": operator_identity_evidence_hash,
            "eligibility_attestation_hash": _hash("GV-ONE-CASE-DELTA:ELIGIBILITY:V1", eligibility),
        },
        occurred_at=occurred_at,
    )
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_BASELINE_OPEN
    body["one_shot_consumed"] = True
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def validate_submission(submission: Submission) -> dict[str, Any]:
    required_lists = (
        "indispensable_missing_evidence",
        "falsifiers_or_contradictions",
        "claim_separation_statements",
        "evidence_locator_ids",
    )
    action = submission.get("current_research_action")
    _require(action in RESEARCH_ACTIONS, "SUBMISSION_ACTION_INVALID")
    rationale = submission.get("rationale")
    _require(isinstance(rationale, str) and rationale.strip(), "SUBMISSION_RATIONALE_REQUIRED")
    for field in required_lists:
        value = submission.get(field)
        _require(isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value), f"SUBMISSION_FIELD_INVALID:{field}")
    _require(set(submission["evidence_locator_ids"]).issubset({"SRC_MU_001", "SRC_NVDA_001"}), "SUBMISSION_LOCATOR_INVALID")
    return {
        "current_research_action": action,
        "rationale": rationale,
        "indispensable_missing_evidence": list(submission["indispensable_missing_evidence"]),
        "falsifiers_or_contradictions": list(submission["falsifiers_or_contradictions"]),
        "claim_separation_statements": list(submission["claim_separation_statements"]),
        "evidence_locator_ids": list(submission["evidence_locator_ids"]),
    }


def _last_event(state: Mapping[str, Any], event_type: str) -> Mapping[str, Any]:
    for event in reversed(state.get("events", [])):
        if event.get("event_type") == event_type:
            return event
    raise OneCaseDeltaError(f"EVENT_NOT_FOUND:{event_type}")


def seal_arm(
    state: Mapping[str, Any], *, arm: str, submission: Submission, occurred_at: str
) -> dict[str, Any]:
    expected_phase = PHASE_BASELINE_OPEN if arm == "BASELINE" else PHASE_POST_OPEN
    open_type = "BASELINE_OPEN" if arm == "BASELINE" else "POST_OPEN"
    sealed_phase = PHASE_BASELINE_SEALED if arm == "BASELINE" else PHASE_POST_SEALED
    _require(state.get("phase") == expected_phase, "ARM_SEAL_PHASE_INVALID")
    opened_at = _last_event(state, open_type)["occurred_at"]
    elapsed_exact = (_parse_timestamp(occurred_at) - _parse_timestamp(opened_at)).total_seconds()
    _require(0 <= elapsed_exact <= MAXIMUM_BUDGET_SECONDS, "ARM_BUDGET_EXCEEDED")
    elapsed = int(elapsed_exact)
    normalized = validate_submission(submission)
    result = _append_event(
        state,
        event_type=f"{arm}_SEAL",
        payload={
            "submission": normalized,
            "submission_hash": _hash(f"GV-ONE-CASE-DELTA:{arm}:SUBMISSION:V1", normalized),
            "elapsed_seconds": elapsed,
            "maximum_budget_seconds": MAXIMUM_BUDGET_SECONDS,
            "early_submission_allowed": True,
            "latency_endpoint": "NONE",
        },
        occurred_at=occurred_at,
    )
    body = _without_hash(result, "session_state_hash")
    body["phase"] = sealed_phase
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def release_projection(
    state: Mapping[str, Any], *, evidence_bundle_hash: str, projection_hash: str, occurred_at: str
) -> dict[str, Any]:
    _require(state.get("phase") == PHASE_BASELINE_SEALED, "PROJECTION_RELEASE_PHASE_INVALID")
    _require(
        evidence_bundle_hash == state.get("bound_evidence_bundle_hash"),
        "EVIDENCE_BUNDLE_SESSION_MISMATCH",
    )
    _require(
        projection_hash == state.get("bound_projection_hash"),
        "PROJECTION_SESSION_MISMATCH",
    )
    result = _append_event(
        state,
        event_type="PROJECTION_RELEASE",
        payload={"evidence_bundle_hash": evidence_bundle_hash, "projection_hash": projection_hash},
        occurred_at=occurred_at,
    )
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_PROJECTION_RELEASED
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def open_post(state: Mapping[str, Any], *, occurred_at: str) -> dict[str, Any]:
    _require(state.get("phase") == PHASE_PROJECTION_RELEASED, "POST_OPEN_PHASE_INVALID")
    result = _append_event(state, event_type="POST_OPEN", payload={}, occurred_at=occurred_at)
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_POST_OPEN
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def consumed_abort(state: Mapping[str, Any], *, reason: str, occurred_at: str) -> dict[str, Any]:
    _require(state.get("one_shot_consumed") is True, "CONSUMED_ABORT_BEFORE_EXPOSURE")
    _require(not str(state.get("phase", "")).startswith("TERMINAL_"), "SESSION_ALREADY_TERMINAL")
    result = _append_event(state, event_type="CONSUMED_ABORT", payload={"reason": reason}, occurred_at=occurred_at)
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_TERMINAL_INELIGIBLE
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def _review_arm(submission: Mapping[str, Any]) -> dict[str, Any]:
    normalized = validate_submission(submission)
    _scan_forbidden(normalized, review=True)
    return normalized


def build_review_package(
    state: Mapping[str, Any], *, random_bit: int | None = None, occurred_at: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _require(state.get("phase") == PHASE_POST_SEALED, "REVIEW_PACKAGE_PHASE_INVALID")
    baseline = _last_event(state, "BASELINE_SEAL")["payload"]["submission"]
    post = _last_event(state, "POST_SEAL")["payload"]["submission"]
    bit = secrets.randbelow(2) if random_bit is None else random_bit
    _require(bit in (0, 1), "RANDOM_BIT_INVALID")
    arm_a, arm_b = (baseline, post) if bit == 0 else (post, baseline)
    mapping_body = {
        "schema_version": SCHEMA_REVIEW_MAPPING,
        "session_manifest_hash": state["session_manifest_hash"],
        "arm_a_origin": "BASELINE" if bit == 0 else "POST",
        "arm_b_origin": "POST" if bit == 0 else "BASELINE",
    }
    mapping = _with_hash(DOMAIN_REVIEW_MAPPING, mapping_body, "review_mapping_hash")
    package_body = {
        "schema_version": SCHEMA_REVIEW_PACKAGE,
        "rubric_items": list(RUBRIC_ITEMS),
        "score_range": [0, 2],
        "arms": {"ARM_A": _review_arm(arm_a), "ARM_B": _review_arm(arm_b)},
    }
    package = _with_hash(DOMAIN_REVIEW_PACKAGE, package_body, "review_package_hash")
    result = _append_event(
        state,
        event_type="REVIEW_PACKAGE_SEAL",
        payload={
            "review_package_hash": package["review_package_hash"],
            "review_mapping_hash": mapping["review_mapping_hash"],
        },
        occurred_at=occurred_at,
    )
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_REVIEW_PACKAGE_SEALED
    return package, mapping, _with_hash(DOMAIN_STATE, body, "session_state_hash")


def _public_key_fingerprint(public_key: str) -> str:
    normalized = " ".join(public_key.strip().split())
    _require(normalized.startswith(("ssh-ed25519 ", "ecdsa-sha2-", "ssh-rsa ")), "SSH_PUBLIC_KEY_INVALID")
    return sha256_bytes((normalized + "\n").encode("utf-8"))


def _verify_sshsig(
    *,
    public_key: str,
    identity: str,
    namespace: str,
    signature: str,
    message: bytes,
    runner: CommandRunner = subprocess.run,
) -> None:
    _require(shutil.which("ssh-keygen") is not None, "SSH_KEYGEN_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="gv-one-case-sshsig-") as tmp:
        root = Path(tmp)
        allowed = root / "allowed_signers"
        signature_path = root / "signature.sshsig"
        allowed.write_text(f"{identity} {public_key.strip()}\n", encoding="utf-8", newline="\n")
        signature_path.write_text(signature.strip() + "\n", encoding="utf-8", newline="\n")
        completed = runner(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed),
                "-I",
                identity,
                "-n",
                namespace,
                "-s",
                str(signature_path),
            ],
            input=message,
            text=False,
            capture_output=True,
            check=False,
        )
    _require(completed.returncode == 0, "SSHSIG_VERIFICATION_FAILED")


def verify_identity_evidence(
    record: Mapping[str, Any],
    *,
    expected_role: str,
    session_manifest: Mapping[str, Any],
    trusted_issuers: Mapping[str, str],
    review_package_hash: str | None = None,
    rubric_digest: str | None = None,
    preflight_only: bool = False,
    runner: CommandRunner = subprocess.run,
) -> str:
    _require(record.get("schema_version") == SCHEMA_IDENTITY, "IDENTITY_SCHEMA_INVALID")
    _require(record.get("adapter") == IDENTITY_ADAPTER, "IDENTITY_ADAPTER_INVALID")
    _require(record.get("role") == expected_role, "IDENTITY_ROLE_INVALID")
    _require(expected_role in {ROLE_OPERATOR, ROLE_REVIEWER}, "IDENTITY_ROLE_UNKNOWN")
    _require(record.get("session_nonce") == session_manifest.get("session_nonce"), "IDENTITY_NONCE_MISMATCH")
    _require(record.get("session_manifest_hash") == session_manifest.get("session_manifest_hash"), "IDENTITY_SESSION_MISMATCH")
    evidence_id = record.get("identity_evidence_id")
    _require(isinstance(evidence_id, str) and evidence_id.strip(), "IDENTITY_EVIDENCE_ID_REQUIRED")
    signed_at = record.get("signed_at")
    _parse_timestamp(signed_at)
    issuer_id = record.get("identity_evidence_issuer")
    _require(isinstance(issuer_id, str) and issuer_id in trusted_issuers, "IDENTITY_ISSUER_UNTRUSTED")
    issuer_public_key = trusted_issuers[issuer_id]
    _require(record.get("issuer_public_key") == issuer_public_key, "IDENTITY_ISSUER_KEY_MISMATCH")
    credential = record.get("credential_public_key")
    _require(isinstance(credential, str), "IDENTITY_CREDENTIAL_REQUIRED")
    fingerprint = _public_key_fingerprint(credential)
    _require(record.get("credential_fingerprint") == fingerprint, "IDENTITY_CREDENTIAL_FINGERPRINT_INVALID")
    _require(record.get("identity_verification_level") == IDENTITY_VERIFICATION_LEVEL, "IDENTITY_VERIFICATION_LEVEL_INVALID")
    subject = record.get("verified_human_subject_commitment")
    _require(isinstance(subject, str) and len(subject) >= 32, "IDENTITY_SUBJECT_COMMITMENT_INVALID")
    principal = record.get("principal_id")
    _require(isinstance(principal, str) and principal.strip(), "IDENTITY_PRINCIPAL_INVALID")

    issuer_claim = record.get("issuer_claim")
    expected_claim = {
        "identity_evidence_id": evidence_id,
        "signed_at": signed_at,
        "verified_human_subject_commitment": subject,
        "principal_id": principal,
        "credential_fingerprint": fingerprint,
        "identity_verification_level": IDENTITY_VERIFICATION_LEVEL,
        "identity_evidence_issuer": issuer_id,
    }
    _require(issuer_claim == expected_claim, "IDENTITY_ISSUER_CLAIM_INVALID")
    _verify_sshsig(
        public_key=issuer_public_key,
        identity=issuer_id,
        namespace=IDENTITY_NAMESPACE,
        signature=record.get("issuer_signature", ""),
        message=canonical_document_bytes(expected_claim),
        runner=runner,
    )

    challenge = {
        "identity_evidence_id": evidence_id,
        "role": expected_role,
        "principal_id": principal,
        "verified_human_subject_commitment": subject,
        "credential_fingerprint": fingerprint,
        "session_nonce": session_manifest["session_nonce"],
        "session_manifest_hash": session_manifest["session_manifest_hash"],
    }
    if expected_role == ROLE_REVIEWER:
        if preflight_only:
            _require(review_package_hash is None and rubric_digest is None, "REVIEWER_PREFLIGHT_BINDING_INVALID")
            challenge.update(
                {
                    "preflight_only": True,
                    "review_package_hash": "PREFLIGHT_PENDING",
                    "rubric_hash": "PREFLIGHT_PENDING",
                }
            )
        else:
            _require(
                isinstance(review_package_hash, str)
                and SHA256_RE.fullmatch(review_package_hash) is not None,
                "REVIEWER_PACKAGE_HASH_REQUIRED",
            )
            _require(
                isinstance(rubric_digest, str)
                and SHA256_RE.fullmatch(rubric_digest) is not None,
                "REVIEWER_RUBRIC_HASH_REQUIRED",
            )
            challenge.update(
                {
                    "preflight_only": False,
                    "review_package_hash": review_package_hash,
                    "rubric_hash": rubric_digest,
                }
            )
    else:
        _require(not preflight_only, "OPERATOR_PREFLIGHT_MODE_INVALID")
        _require(review_package_hash is None and rubric_digest is None, "OPERATOR_REVIEW_BINDING_PROHIBITED")
    _require(record.get("role_specific_challenge") == challenge, "IDENTITY_ROLE_CHALLENGE_INVALID")
    _verify_sshsig(
        public_key=credential,
        identity=principal,
        namespace=ROLE_NAMESPACE,
        signature=record.get("role_signature", ""),
        message=canonical_document_bytes(challenge),
        runner=runner,
    )
    body = dict(record)
    body.pop("identity_evidence_hash", None)
    identity_hash = _hash(DOMAIN_IDENTITY, body)
    stored = record.get("identity_evidence_hash")
    if stored is not None:
        _require(stored == identity_hash, "IDENTITY_EVIDENCE_HASH_INVALID")
    return identity_hash


def require_distinct_humans(operator: Mapping[str, Any], reviewer: Mapping[str, Any]) -> None:
    _require(operator.get("role") == ROLE_OPERATOR and reviewer.get("role") == ROLE_REVIEWER, "HUMAN_ROLE_PAIR_INVALID")
    _require(operator.get("verified_human_subject_commitment") != reviewer.get("verified_human_subject_commitment"), "SAME_HUMAN_SUBJECT_PROHIBITED")
    _require(operator.get("credential_fingerprint") != reviewer.get("credential_fingerprint"), "SAME_HUMAN_CREDENTIAL_PROHIBITED")
    _require(operator.get("principal_id") != reviewer.get("principal_id"), "SAME_PRINCIPAL_PROHIBITED")


def rubric_hash(scores: Mapping[str, Mapping[str, int]]) -> str:
    _validate_scores(scores)
    return _hash(DOMAIN_RUBRIC, scores)


def _validate_scores(scores: Mapping[str, Mapping[str, int]]) -> None:
    _require(set(scores) == {"ARM_A", "ARM_B"}, "RUBRIC_ARMS_INVALID")
    for arm_scores in scores.values():
        _require(set(arm_scores) == set(RUBRIC_ITEMS), "RUBRIC_ITEMS_INVALID")
        _require(all(isinstance(value, int) and 0 <= value <= 2 for value in arm_scores.values()), "RUBRIC_SCORE_INVALID")


def validate_session_attestation(
    record: Mapping[str, Any],
    *,
    session_manifest_hash: str,
    sealed_record_hashes: Sequence[str],
    review_package_hash: str,
    rubric_digest: str,
    operator_identity_evidence_hash: str,
    reviewer_identity_evidence_hash: str,
    runner: CommandRunner = subprocess.run,
) -> str:
    _require(record.get("schema_version") == SCHEMA_ATTESTATION, "ATTESTATION_SCHEMA_INVALID")
    _require(record.get("adapter") == IDENTITY_ADAPTER, "ATTESTATION_ADAPTER_INVALID")
    payload = {
        "session_manifest_hash": session_manifest_hash,
        "sealed_record_hashes": list(sealed_record_hashes),
        "review_package_hash": review_package_hash,
        "rubric_hash": rubric_digest,
        "operator_identity_evidence_hash": operator_identity_evidence_hash,
        "reviewer_identity_evidence_hash": reviewer_identity_evidence_hash,
        "attestation_statements": record.get("attestation_statements"),
        "attestation_id": record.get("attestation_id"),
        "attestation_provider": record.get("attestation_provider"),
    }
    _require(record.get("payload") == payload, "ATTESTATION_PAYLOAD_INVALID")
    public_key = record.get("attestor_public_key")
    attestor_id = record.get("attestor_id")
    _require(isinstance(public_key, str) and isinstance(attestor_id, str), "ATTESTOR_IDENTITY_INVALID")
    _verify_sshsig(
        public_key=public_key,
        identity=attestor_id,
        namespace=ATTESTATION_NAMESPACE,
        signature=record.get("signature", ""),
        message=canonical_document_bytes(payload),
        runner=runner,
    )
    body = dict(record)
    body.pop("session_attestation_hash", None)
    digest = _hash(DOMAIN_ATTESTATION, body)
    stored = record.get("session_attestation_hash")
    if stored is not None:
        _require(stored == digest, "ATTESTATION_HASH_INVALID")
    return digest


def decision_value_disposition(
    *, baseline_scores: Mapping[str, int], post_scores: Mapping[str, int]
) -> tuple[str, dict[str, int]]:
    _validate_scores({"ARM_A": baseline_scores, "ARM_B": post_scores})
    deltas = {item: post_scores[item] - baseline_scores[item] for item in RUBRIC_ITEMS}
    total = sum(deltas.values())
    targeted_gain = any(deltas[item] > 0 for item in TARGETED_DIMENSIONS)
    safety_not_worse = all(deltas[item] >= 0 for item in CORE_SAFETY_DIMENSIONS)
    disposition = "IMPROVED" if total > 0 and targeted_gain and safety_not_worse else "NOT_IMPROVED"
    return disposition, deltas


def sealed_record_hashes(state: Mapping[str, Any]) -> list[str]:
    verify_event_chain(state)
    return [event["event_hash"] for event in state["events"]]


def seal_review_authority(
    *,
    state: Mapping[str, Any],
    session_manifest: Mapping[str, Any],
    review_package: Mapping[str, Any],
    scores: Mapping[str, Mapping[str, int]],
    operator_identity_evidence: Mapping[str, Any],
    reviewer_identity_evidence: Mapping[str, Any],
    trusted_issuers: Mapping[str, str],
    session_attestation: Mapping[str, Any],
    occurred_at: str,
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    verify_event_chain(state)
    _require(state.get("phase") == PHASE_REVIEW_PACKAGE_SEALED, "REVIEW_AUTHORITY_PHASE_INVALID")
    _validate_embedded_hash(
        session_manifest,
        domain=DOMAIN_SESSION_MANIFEST,
        field="session_manifest_hash",
        code="SESSION_MANIFEST_HASH_INVALID",
    )
    _require(
        state.get("session_manifest_hash") == session_manifest.get("session_manifest_hash"),
        "REVIEW_AUTHORITY_SESSION_MISMATCH",
    )
    _validate_embedded_hash(
        review_package,
        domain=DOMAIN_REVIEW_PACKAGE,
        field="review_package_hash",
        code="REVIEW_PACKAGE_HASH_INVALID",
    )
    package_event = _last_event(state, "REVIEW_PACKAGE_SEAL")
    _require(
        package_event["payload"].get("review_package_hash")
        == review_package.get("review_package_hash"),
        "REVIEW_PACKAGE_EVENT_MISMATCH",
    )
    _validate_scores(scores)
    digest = rubric_hash(scores)
    operator_hash = verify_identity_evidence(
        operator_identity_evidence,
        expected_role=ROLE_OPERATOR,
        session_manifest=session_manifest,
        trusted_issuers=trusted_issuers,
        runner=runner,
    )
    baseline_event = _last_event(state, "BASELINE_OPEN")
    _require(
        baseline_event["payload"].get("operator_identity_evidence_hash") == operator_hash,
        "OPERATOR_IDENTITY_CHANGED_AFTER_EXPOSURE",
    )
    reviewer_hash = verify_identity_evidence(
        reviewer_identity_evidence,
        expected_role=ROLE_REVIEWER,
        session_manifest=session_manifest,
        trusted_issuers=trusted_issuers,
        review_package_hash=review_package["review_package_hash"],
        rubric_digest=digest,
        runner=runner,
    )
    require_distinct_humans(operator_identity_evidence, reviewer_identity_evidence)
    record_hashes = sealed_record_hashes(state)
    attestation_hash = validate_session_attestation(
        session_attestation,
        session_manifest_hash=session_manifest["session_manifest_hash"],
        sealed_record_hashes=record_hashes,
        review_package_hash=review_package["review_package_hash"],
        rubric_digest=digest,
        operator_identity_evidence_hash=operator_hash,
        reviewer_identity_evidence_hash=reviewer_hash,
        runner=runner,
    )
    result = _append_event(
        state,
        event_type="REVIEW_AUTHORITY_SEAL",
        payload={
            "scores": {arm: dict(arm_scores) for arm, arm_scores in scores.items()},
            "rubric_hash": digest,
            "operator_identity_evidence_hash": operator_hash,
            "reviewer_identity_evidence_hash": reviewer_hash,
            "session_attestation_hash": attestation_hash,
            "sealed_record_hashes": record_hashes,
        },
        occurred_at=occurred_at,
    )
    body = _without_hash(result, "session_state_hash")
    body["phase"] = PHASE_REVIEW_AUTHORITY_SEALED
    return _with_hash(DOMAIN_STATE, body, "session_state_hash")


def reveal_mapping_and_finalize(
    *,
    state: Mapping[str, Any],
    review_package: Mapping[str, Any],
    review_mapping: Mapping[str, Any],
    occurred_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify_event_chain(state)
    _require(state.get("phase") == PHASE_REVIEW_AUTHORITY_SEALED, "MAPPING_REVEAL_PHASE_INVALID")
    _validate_embedded_hash(
        review_package,
        domain=DOMAIN_REVIEW_PACKAGE,
        field="review_package_hash",
        code="REVIEW_PACKAGE_HASH_INVALID",
    )
    _validate_embedded_hash(
        review_mapping,
        domain=DOMAIN_REVIEW_MAPPING,
        field="review_mapping_hash",
        code="REVIEW_MAPPING_HASH_INVALID",
    )
    _require(
        review_mapping.get("session_manifest_hash") == state.get("session_manifest_hash"),
        "REVIEW_MAPPING_SESSION_MISMATCH",
    )
    package_event = _last_event(state, "REVIEW_PACKAGE_SEAL")
    _require(
        package_event["payload"].get("review_package_hash")
        == review_package.get("review_package_hash"),
        "REVIEW_PACKAGE_EVENT_MISMATCH",
    )
    _require(
        package_event["payload"].get("review_mapping_hash")
        == review_mapping.get("review_mapping_hash"),
        "REVIEW_MAPPING_EVENT_MISMATCH",
    )
    origins = {review_mapping.get("arm_a_origin"), review_mapping.get("arm_b_origin")}
    _require(origins == {"BASELINE", "POST"}, "REVIEW_MAPPING_ORIGINS_INVALID")
    authority = _last_event(state, "REVIEW_AUTHORITY_SEAL")["payload"]
    scores = authority.get("scores")
    _validate_scores(scores)
    _require(rubric_hash(scores) == authority.get("rubric_hash"), "SEALED_RUBRIC_HASH_INVALID")
    mapping = {
        review_mapping["arm_a_origin"]: "ARM_A",
        review_mapping["arm_b_origin"]: "ARM_B",
    }
    baseline_scores = scores[mapping["BASELINE"]]
    post_scores = scores[mapping["POST"]]
    disposition, deltas = decision_value_disposition(
        baseline_scores=baseline_scores, post_scores=post_scores
    )
    revealed = _append_event(
        state,
        event_type="MAPPING_REVEAL",
        payload={
            "review_mapping": dict(review_mapping),
            "review_mapping_hash": review_mapping["review_mapping_hash"],
        },
        occurred_at=occurred_at,
    )
    terminal_body = _without_hash(revealed, "session_state_hash")
    terminal_body["phase"] = PHASE_TERMINAL_ELIGIBLE
    terminal_state = _with_hash(DOMAIN_STATE, terminal_body, "session_state_hash")
    result_body = {
        "schema_version": SCHEMA_RESULT,
        "session_manifest_hash": state["session_manifest_hash"],
        "terminal_session_state_hash": terminal_state["session_state_hash"],
        "eligible": True,
        "observation_class": OBSERVATION_CLASS,
        "observed_comparison_count": 1,
        "decision_value_disposition": disposition,
        "rubric_scores": {"baseline": dict(baseline_scores), "post": dict(post_scores)},
        "rubric_deltas": deltas,
        "total_delta": sum(deltas.values()),
        "review_package_hash": review_package["review_package_hash"],
        "review_mapping_hash": review_mapping["review_mapping_hash"],
        "rubric_hash": authority["rubric_hash"],
        "operator_identity_evidence_hash": authority["operator_identity_evidence_hash"],
        "reviewer_identity_evidence_hash": authority["reviewer_identity_evidence_hash"],
        "session_attestation_hash": authority["session_attestation_hash"],
        "score_change": 0,
        "alpha_claim": False,
        "publication_authority": False,
    }
    result = _with_hash(DOMAIN_RESULT, result_body, "result_hash")
    return result, terminal_state
