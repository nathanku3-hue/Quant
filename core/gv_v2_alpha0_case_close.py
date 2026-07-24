"""GV-ALPHA0-CLOSE — one multi-source case vertical (walking skeleton → harden).

Audit locks (REPAIR_AND_SHIP_CURRENT_SLICE):
  - score stays 39; observed stays 0
  - operable shipment stage → CERTIFIED_MULTI_SOURCE_CASE_OPERABLE only after
    sealed pre-adjudication + explicit operator confirmation + certify
  - coverage=PARTIAL describes evidence *overlap*, not claim sufficiency
  - claim=CLAIM_INSUFFICIENT always for this Alpha case
  - research=HOLD_FOR_EVIDENCE; portfolio=NO_POSITION invariantly (paper)
  - Case Workspace captures an explicit confirm action (self-labelled) —
    not trusted identity or discretionary decision; never auto-build on load
  - evidence cannot force a position without price-consistent expectations,
    business capture, and economics — Alpha remains paper NO_POSITION
  - publish current / truth cutover / tag only after rebuild+adversarial+
    fresh-clone/dogfood (publish defaults False)
  - product entrypoint is broker-free (alpha_app / launch_alpha)

Vertical:

  both-family raw rebuild → sealed pre-adjudication
  (manifest + coverage + claim + both-source excerpts/locators/overlap)
  → explicit operator confirmation persisted
  → Case Workspace adjudication → certified result
  → export/replay → (later) publish
"""

from __future__ import annotations

import json
import shutil
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from core.gv_fs0_book import (
    DecisionEnvelope,
    _build_book,
    _build_decision,
    build_no_position_source_fixture,
)
from core.gv_fs0_canonical import domain_hash, parse_json_text
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
from core.gv_v2_alpha0_source_family_two import (
    FAMILY_ONE_ID,
    SOURCE_FAMILY_ID as FAMILY_TWO_ID,
    extract_case_facts as sf2_extract_facts,
    load_access_authorization as sf2_load_auth,
    build_package_manifest as sf2_build_package,
    run_admission_checks as sf2_run_admission,
)
from core.gv_v2_b0b_official_source_intake import (
    SOURCE_FAMILY_ID as FAMILY_ONE_SOURCE_ID,
    rebuild_canonical_b0b_chain,
)

VerifierRunner = Callable[[Mapping[str, Any]], dict[str, Any]]

ROOT = Path(__file__).resolve().parents[1]

CASE_ID = "V2_ALPHA0_MU_G_SUPPLY_CLOSE_1"
SUBJECT_CASE = "MU_G_SUPPLY"
MODULE = "G_supply"
DECISION_ID = "DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1"
SLICE_CLASSIFICATION = "GV-ALPHA0-CLOSE"
FUNCTIONAL_STAGE_PRE_ADJUDICATION = "MULTI_SOURCE_CASE_SEALED_PRE_ADJUDICATION"
# Offline bank tooling may certify paper artifacts, but OPERABLE is dogfood-only.
FUNCTIONAL_STAGE_BANKED = "CERTIFIED_MULTI_SOURCE_CASE_BANKED"
FUNCTIONAL_STAGE_OPERABLE = "CERTIFIED_MULTI_SOURCE_CASE_OPERABLE"
# Alias retained for imports; means dogfood-earned operable stage only.
FUNCTIONAL_STAGE = FUNCTIONAL_STAGE_OPERABLE
SHIPPED_PRODUCT_SCORE = 39
OBSERVED_COMPARISON_COUNT = 0

RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"
CLAIM_OUTCOME_INSUFFICIENT = "CLAIM_INSUFFICIENT"
COVERAGE_PARTIAL = "PARTIAL"
ADJUDICATION_KIND = "CASE_WORKSPACE_ADJUDICATION"
PERMITTED_PORTFOLIO_ACTIONS: tuple[str, ...] = (PORTFOLIO_ACTION_NO_POSITION,)
OPERATOR_CONFIRMATION_PHRASE = "CONFIRM_NO_POSITION"
CAPTURE_SURFACE_UI = "CASE_WORKSPACE_UI"
CAPTURE_SURFACE_OFFLINE = "OFFLINE_BANK_TOOL"

CASE_MANIFEST_DOMAIN = "GV-ALPHA0:CASE_MANIFEST:V1"
COVERAGE_DOMAIN = "GV-ALPHA0:COVERAGE:V1"
CLAIM_DOMAIN = "GV-ALPHA0:CASE_CLAIM:V1"
EVIDENCE_PANEL_DOMAIN = "GV-ALPHA0:EVIDENCE_PANEL:V1"
PRE_ADJUDICATION_DOMAIN = "GV-ALPHA0:PRE_ADJUDICATION_SEAL:V1"
OPERATOR_CONFIRMATION_DOMAIN = "GV-ALPHA0:OPERATOR_CONFIRMATION:V1"
ADJUDICATION_DOMAIN = "GV-ALPHA0:ADJUDICATION:V1"
RESEARCH_DOMAIN = "GV-ALPHA0:CASE_RESEARCH:V1"
RESULT_DOMAIN = "GV-ALPHA0:CASE_RESULT:V1"
EXPORT_DOMAIN = "GV-ALPHA0:CASE_EXPORT:V1"

CASE_DIR = ROOT / "data" / "gv_v2_alpha0" / "case_mu_g_supply_close_1"

# Frozen evaluation cutoff for this Alpha case (PIT wall; not a live clock).
CASE_CUTOFF_AT = "2026-07-23T00:00:00.000000Z"
CASE_CUTOFF_NOTE = (
    "Evaluation cutoff freezes which banked family artifacts may enter this case. "
    "Receipt times on family packages must be <= cutoff."
)

CLAIM_BOUNDARY = (
    "GV-ALPHA0-CLOSE multi-source case for MU G_supply. "
    "coverage=PARTIAL describes evidence overlap only — not claim sufficiency. "
    "claim remains CLAIM_INSUFFICIENT. "
    "Case Workspace adjudication is self-labelled selection of the sole permitted "
    "paper action NO_POSITION — not trusted identity and not discretionary sizing. "
    "Evidence cannot authorize a position without price-consistent expectations, "
    "business capture, and economics; Alpha portfolio action is invariantly "
    "paper NO_POSITION. Score 39 frozen; observed 0; formal comparison deferred."
)

# Explicit overlap: only memory-price industry language spans families in this bank.
OVERLAP_PAIRS: tuple[dict[str, str], ...] = (
    {
        "overlap_id": "OVLP_MEMORY_PRICES_001",
        "family_one_statement_id": "B0B_STMT_CONSTRAINED_SUPPLY_001",
        "family_two_fact_id": "SF2_FACT_MEMORY_PRICES_001",
        "overlap_class": "INDUSTRY_PRICING_LANGUAGE",
        "note": (
            "MU constrained-supply/pricing language and NVDA elevated memory and "
            "systems prices are partial industry-context overlap only."
        ),
    },
)


class GvAlpha0CloseError(ValueError):
    """Fail-closed Alpha close errors."""


def _plain(obj: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical_json_bytes(payload)
    tmp = path.with_name(f".{path.name}.tmp_{uuid.uuid4().hex}")
    try:
        tmp.write_bytes(raw)
        if tmp.read_bytes() != raw:
            raise GvAlpha0CloseError(f"ALPHA0_CLOSE_WRITE_VERIFY_FAILED:{path.name}")
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _load_json(path: Path, *, missing_code: str) -> dict[str, Any]:
    if not path.is_file():
        raise GvAlpha0CloseError(missing_code)
    return parse_json_text(path.read_text(encoding="utf-8"))


def _atomic_write_case_bundle(
    out_dir: Path,
    artifacts: Mapping[str, Mapping[str, Any] | str],
    *,
    promote_order: tuple[str, ...],
) -> None:
    """Result-last fail-closed promote (not multi-file rollback atomicity)."""

    if set(artifacts) != set(promote_order):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CASE_BUNDLE_ORDER_MISMATCH")
    out_dir.mkdir(parents=True, exist_ok=True)
    staging_root = out_dir / ".alpha0_close_tx"
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
                raise GvAlpha0CloseError(f"ALPHA0_CLOSE_WRITE_VERIFY_FAILED:{name}")
            staged[name] = raw
        for name in promote_order:
            raw = staged[name]
            final = out_dir / name
            tmp = out_dir / f".{name}.promotetmp"
            tmp.write_bytes(raw)
            tmp.replace(final)
            if final.read_bytes() != raw:
                raise GvAlpha0CloseError(f"ALPHA0_CLOSE_WRITE_VERIFY_FAILED:{name}")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        try:
            if staging_root.is_dir() and not any(staging_root.iterdir()):
                staging_root.rmdir()
        except OSError:
            pass


def load_family_pins(*, root: Path | None = None) -> dict[str, Any]:
    """Rebuild both banked families and return pin hashes (bind by hash, not ID alone)."""

    base = Path(root) if root is not None else ROOT
    b0b = rebuild_canonical_b0b_chain(root=base, include_result=False)
    if b0b["admission"].get("status") != "ADMITTED":
        raise GvAlpha0CloseError("ALPHA0_CLOSE_FAMILY_ONE_NOT_ADMITTED")
    if b0b["claim"].get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_FAMILY_ONE_CLAIM_UNEXPECTED")

    sf2_auth = sf2_load_auth(root=base)
    sf2_package = sf2_build_package(root=base, access_authorization=sf2_auth)
    sf2_admission = sf2_run_admission(
        root=base, access_authorization=sf2_auth, package_manifest=sf2_package
    )
    if sf2_admission.get("status") != "ADMITTED":
        raise GvAlpha0CloseError("ALPHA0_CLOSE_FAMILY_TWO_NOT_ADMITTED")
    sf2_facts = sf2_extract_facts(
        root=base, admission=sf2_admission, package_manifest=sf2_package
    )

    family_one = {
        "source_family_id": FAMILY_ONE_SOURCE_ID,
        "family_case_id": b0b["package_manifest"]["case_id"],
        "access_authorization_hash": b0b["access_authorization"]["authorization_hash"],
        "package_manifest_hash": b0b["package_manifest"]["package_manifest_hash"],
        "source_manifest_hash": b0b["source_manifest"]["source_manifest_hash"],
        "admission_hash": b0b["admission"]["admission_hash"],
        "claim_evaluation_hash": b0b["claim"]["claim_evaluation_hash"],
        "admission_status": b0b["admission"]["status"],
        "package_retrieved_at": b0b["package_manifest"]["retrieved_at"],
    }
    family_two = {
        "source_family_id": FAMILY_TWO_ID,
        "family_case_id": sf2_package["case_id"],
        "access_authorization_hash": sf2_auth["authorization_hash"],
        "package_manifest_hash": sf2_package["package_manifest_hash"],
        "admission_hash": sf2_admission["admission_hash"],
        "fact_set_hash": sf2_facts["fact_set_hash"],
        "fact_count": sf2_facts["fact_count"],
        "admission_status": sf2_admission["status"],
        "package_retrieved_at": sf2_package["retrieved_at"],
    }
    if family_one["source_family_id"] != FAMILY_ONE_ID:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_FAMILY_ONE_ID_MISMATCH")
    return {
        "family_one": family_one,
        "family_two": family_two,
        "b0b": b0b,
        "sf2": {
            "access_authorization": sf2_auth,
            "package_manifest": sf2_package,
            "admission": sf2_admission,
            "fact_set": sf2_facts,
        },
    }


def build_case_manifest(
    *,
    root: Path | None = None,
    family_pins: Mapping[str, Any] | None = None,
    cutoff_at: str = CASE_CUTOFF_AT,
) -> dict[str, Any]:
    """One manifest containing cutoff and both-family hashes."""

    pins = _plain(family_pins) if family_pins is not None else load_family_pins(root=root)
    f1 = pins["family_one"]
    f2 = pins["family_two"]
    for label, retrieved in (
        ("family_one", f1["package_retrieved_at"]),
        ("family_two", f2["package_retrieved_at"]),
    ):
        if str(retrieved) > cutoff_at:
            raise GvAlpha0CloseError(f"ALPHA0_CLOSE_CUTOFF_VIOLATION:{label}")

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_case_manifest_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "module": MODULE,
        "cutoff": {
            "cutoff_at": cutoff_at,
            "cutoff_note": CASE_CUTOFF_NOTE,
        },
        "family_one": {
            "source_family_id": f1["source_family_id"],
            "family_case_id": f1["family_case_id"],
            "access_authorization_hash": f1["access_authorization_hash"],
            "package_manifest_hash": f1["package_manifest_hash"],
            "source_manifest_hash": f1["source_manifest_hash"],
            "admission_hash": f1["admission_hash"],
            "claim_evaluation_hash": f1["claim_evaluation_hash"],
            "admission_status": f1["admission_status"],
        },
        "family_two": {
            "source_family_id": f2["source_family_id"],
            "family_case_id": f2["family_case_id"],
            "access_authorization_hash": f2["access_authorization_hash"],
            "package_manifest_hash": f2["package_manifest_hash"],
            "admission_hash": f2["admission_hash"],
            "fact_set_hash": f2["fact_set_hash"],
            "fact_count": f2["fact_count"],
            "admission_status": f2["admission_status"],
        },
        "independent_source_count": 2,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["case_manifest_hash"] = domain_hash(CASE_MANIFEST_DOMAIN, body)
    return body


def build_coverage_assessment(
    case_manifest: Mapping[str, Any],
    *,
    family_pins: Mapping[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """PARTIAL = evidence overlap description only — not claim sufficiency."""

    pins = _plain(family_pins) if family_pins is not None else load_family_pins(root=root)
    f1_ids = {
        s["statement_id"] for s in pins["b0b"]["claim"]["statements"]
    }
    f2_ids = {f["fact_id"] for f in pins["sf2"]["fact_set"]["facts"]}
    pairs: list[dict[str, str]] = []
    for pair in OVERLAP_PAIRS:
        if pair["family_one_statement_id"] not in f1_ids:
            raise GvAlpha0CloseError("ALPHA0_CLOSE_OVERLAP_FAMILY_ONE_MISSING")
        if pair["family_two_fact_id"] not in f2_ids:
            raise GvAlpha0CloseError("ALPHA0_CLOSE_OVERLAP_FAMILY_TWO_MISSING")
        pairs.append(dict(pair))

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_coverage_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_status": COVERAGE_PARTIAL,
        "coverage_meaning": (
            "PARTIAL describes evidence *overlap* across independent source "
            "families. It does not assert claim sufficiency, thesis truth, "
            "physical supply identification, investability, or position authority."
        ),
        "overlap_pairs": pairs,
        "overlap_count": len(pairs),
        "non_overlap_notes": [
            "NVDA foundry/NCNR disclosures are peer/customer supply-chain risk, "
            "not Micron issuer corroboration.",
            "MU facility/expansion disclosures have no paired NVDA fact in this case.",
            "No physical-supply telemetry bytes are present on either family.",
        ],
        "independent_source_count": 2,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["coverage_hash"] = domain_hash(COVERAGE_DOMAIN, body)
    return body


def build_case_claim(
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    """Claim sufficiency is separate from coverage. Always CLAIM_INSUFFICIENT here."""

    if coverage.get("coverage_status") != COVERAGE_PARTIAL:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_COVERAGE_UNEXPECTED")
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_case_claim_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "module": MODULE,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "coverage_status": coverage["coverage_status"],
        "claim_outcome": CLAIM_OUTCOME_INSUFFICIENT,
        "evidence_dimensions": {
            "official_filings_admitted": "PASS",
            "evidence_overlap_coverage": "PARTIAL",
            "independent_source_corroboration_for_thesis": "FAIL",
            "physical_supply_telemetry": "FAIL",
            "price_consistent_expectations": "NOT_EVALUATED",
            "business_capture": "NOT_EVALUATED",
            "economics": "NOT_EVALUATED",
            "sufficient_for_research_advancement": "FAIL",
        },
        "evaluation_notes": [
            "coverage=PARTIAL is not claim sufficiency.",
            "Independent filings admitted; industry-pricing overlap only.",
            "No price-consistent expectations, business capture, or economics "
            "evaluation — position authority remains unavailable.",
            "Derivation: insufficient for research advancement → CLAIM_INSUFFICIENT.",
        ],
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["case_claim_hash"] = domain_hash(CLAIM_DOMAIN, body)
    return body


def _locator_excerpt_fields(row: Mapping[str, Any], *, id_key: str) -> dict[str, Any]:
    return {
        id_key: row[id_key],
        "document_locator": row["document_locator"],
        "official_locator": row["official_locator"],
        "section_or_element_locator": row["section_or_element_locator"],
        "byte_start": row["byte_start"],
        "byte_end": row["byte_end"],
        "exact_excerpt": row["exact_excerpt"],
        "exact_excerpt_hash": row["exact_excerpt_hash"],
        "source_object_hash": row["source_object_hash"],
        "source_family_id": row["source_family_id"],
    }


def build_evidence_panel(
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    *,
    family_pins: Mapping[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Both-source excerpts + locators + overlap for sealed pre-adjudication display."""

    pins = _plain(family_pins) if family_pins is not None else load_family_pins(root=root)
    f1_by_id = {
        s["statement_id"]: s for s in pins["b0b"]["claim"]["statements"]
    }
    f2_by_id = {f["fact_id"]: f for f in pins["sf2"]["fact_set"]["facts"]}
    panels: list[dict[str, Any]] = []
    for pair in coverage["overlap_pairs"]:
        s1 = f1_by_id.get(pair["family_one_statement_id"])
        f2 = f2_by_id.get(pair["family_two_fact_id"])
        if s1 is None:
            raise GvAlpha0CloseError("ALPHA0_CLOSE_EVIDENCE_FAMILY_ONE_MISSING")
        if f2 is None:
            raise GvAlpha0CloseError("ALPHA0_CLOSE_EVIDENCE_FAMILY_TWO_MISSING")
        panels.append(
            {
                "overlap_id": pair["overlap_id"],
                "overlap_class": pair["overlap_class"],
                "note": pair["note"],
                "family_one": _locator_excerpt_fields(s1, id_key="statement_id"),
                "family_two": _locator_excerpt_fields(f2, id_key="fact_id"),
            }
        )
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_evidence_panel_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "coverage_status": coverage["coverage_status"],
        "overlap_count": len(panels),
        "overlap_panels": panels,
        "non_overlap_notes": list(coverage.get("non_overlap_notes") or []),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["evidence_panel_hash"] = domain_hash(EVIDENCE_PANEL_DOMAIN, body)
    return body


def build_pre_adjudication_seal(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    evidence_panel: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal pre-adjudication package — no adjudication, no certification."""

    if case_claim.get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_SEAL_REQUIRES_INSUFFICIENT_CLAIM")
    if coverage.get("coverage_status") != COVERAGE_PARTIAL:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_SEAL_REQUIRES_PARTIAL_COVERAGE")
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_pre_adjudication_seal_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "functional_stage": FUNCTIONAL_STAGE_PRE_ADJUDICATION,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "evidence_panel_hash": evidence_panel["evidence_panel_hash"],
        "cutoff_at": case_manifest["cutoff"]["cutoff_at"],
        "family_one_source_family_id": case_manifest["family_one"]["source_family_id"],
        "family_two_source_family_id": case_manifest["family_two"]["source_family_id"],
        "coverage_status": coverage["coverage_status"],
        "claim_outcome": case_claim["claim_outcome"],
        "permitted_portfolio_actions": list(PERMITTED_PORTFOLIO_ACTIONS),
        "adjudication_present": False,
        "certification_status": None,
        "shipped_product_score": SHIPPED_PRODUCT_SCORE,
        "observed_comparison_count": OBSERVED_COMPARISON_COUNT,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["pre_adjudication_seal_hash"] = domain_hash(PRE_ADJUDICATION_DOMAIN, body)
    return body


def build_operator_confirmation(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    pre_adjudication_seal: Mapping[str, Any],
    adjudicator_label: str,
    confirmed_at: str,
    confirmation_phrase: str = OPERATOR_CONFIRMATION_PHRASE,
    selected_action: str = PORTFOLIO_ACTION_NO_POSITION,
    capture_surface: str = CAPTURE_SURFACE_UI,
) -> dict[str, Any]:
    """Explicit operator confirmation — required before certification."""

    if confirmation_phrase != OPERATOR_CONFIRMATION_PHRASE:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRMATION_PHRASE_MISMATCH")
    if selected_action not in PERMITTED_PORTFOLIO_ACTIONS:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ACTION_NOT_PERMITTED")
    if selected_action != PORTFOLIO_ACTION_NO_POSITION:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_POSITION_FORBIDDEN")
    if not adjudicator_label or not isinstance(adjudicator_label, str):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ADJUDICATOR_LABEL_REQUIRED")
    if case_claim.get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRM_REQUIRES_INSUFFICIENT_CLAIM")
    if (
        pre_adjudication_seal.get("case_claim_hash")
        != case_claim["case_claim_hash"]
    ):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRM_SEAL_MISMATCH")

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_operator_confirmation_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "confirmed": True,
        "confirmation_phrase": confirmation_phrase,
        "selected_action": selected_action,
        "research_stance": RESEARCH_ACTION_HOLD,
        "adjudicator_label": adjudicator_label,
        "adjudicator_identity_claim": "SELF_LABELLED_ONLY",
        "trusted_identity": False,
        "discretionary_decision": False,
        "confirmed_at": confirmed_at,
        "capture_surface": capture_surface,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "pre_adjudication_seal_hash": pre_adjudication_seal[
            "pre_adjudication_seal_hash"
        ],
        "decision_id": DECISION_ID,
        "notes": (
            "Operator explicitly confirmed the sole permitted paper action "
            "NO_POSITION against a sealed pre-adjudication case. "
            "Self-labelled only — not trusted identity."
        ),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["operator_confirmation_hash"] = domain_hash(
        OPERATOR_CONFIRMATION_DOMAIN, body
    )
    return body


def capture_case_workspace_adjudication(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    operator_confirmation: Mapping[str, Any],
    adjudicator_label: str | None = None,
    adjudicated_at: str | None = None,
    selected_action: str | None = None,
) -> dict[str, Any]:
    """Record Case Workspace adjudication from a persisted operator confirmation."""

    if case_claim.get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ADJUDICATION_REQUIRES_INSUFFICIENT_CLAIM")
    if not operator_confirmation.get("confirmed"):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ADJUDICATION_REQUIRES_CONFIRMATION")
    if (
        operator_confirmation.get("confirmation_phrase")
        != OPERATOR_CONFIRMATION_PHRASE
    ):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRMATION_PHRASE_MISMATCH")
    if (
        operator_confirmation.get("case_claim_hash")
        != case_claim["case_claim_hash"]
    ):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRM_CLAIM_MISMATCH")

    label = adjudicator_label or str(operator_confirmation["adjudicator_label"])
    when = adjudicated_at or str(operator_confirmation["confirmed_at"])
    action = selected_action or str(operator_confirmation["selected_action"])
    if action not in PERMITTED_PORTFOLIO_ACTIONS:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ACTION_NOT_PERMITTED")
    if not label or not isinstance(label, str):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_ADJUDICATOR_LABEL_REQUIRED")
    if action != PORTFOLIO_ACTION_NO_POSITION:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_POSITION_FORBIDDEN")

    rationale_ref = f"ALPHA0:CLOSE:CLM:{case_claim['case_claim_hash']}"
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_adjudication_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "adjudication_kind": ADJUDICATION_KIND,
        "adjudicator_label": label,
        "adjudicator_identity_claim": "SELF_LABELLED_ONLY",
        "trusted_identity": False,
        "discretionary_decision": False,
        "permitted_portfolio_actions": list(PERMITTED_PORTFOLIO_ACTIONS),
        "selected_action": action,
        "research_stance": RESEARCH_ACTION_HOLD,
        "adjudicated_at": when,
        "decision_id": DECISION_ID,
        "rationale_ref": rationale_ref,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "operator_confirmation_hash": operator_confirmation[
            "operator_confirmation_hash"
        ],
        "notes": (
            "Self-labelled human confirmed the sole permitted paper action "
            "NO_POSITION after reviewing sealed both-source excerpts. "
            "This is adjudication of an already-constrained outcome, not trusted "
            "identity proof and not discretionary portfolio choice."
        ),
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["adjudication_hash"] = domain_hash(ADJUDICATION_DOMAIN, body)
    return body


def build_research_decision(
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    if adjudication.get("selected_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_NON_NO_POSITION_NOT_AUTHORIZED")
    if adjudication.get("research_stance") != RESEARCH_ACTION_HOLD:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_NON_HOLD_NOT_AUTHORIZED")
    if case_claim.get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CLAIM_MUST_BE_INSUFFICIENT")

    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_case_research_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "module": MODULE,
        "research_action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "portfolio_action_invariant": True,
        "decision_id": DECISION_ID,
        "rationale_ref": adjudication["rationale_ref"],
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "coverage_status": coverage["coverage_status"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "claim_outcome": case_claim["claim_outcome"],
        "adjudication_hash": adjudication["adjudication_hash"],
        "independent_source_count": 2,
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


def functional_stage_for_confirmation(
    operator_confirmation: Mapping[str, Any] | None,
) -> str:
    """OPERABLE is earned only by Case Workspace UI dogfood confirmation."""

    if operator_confirmation is None:
        return FUNCTIONAL_STAGE_PRE_ADJUDICATION
    surface = str(operator_confirmation.get("capture_surface") or "")
    if surface == CAPTURE_SURFACE_UI:
        return FUNCTIONAL_STAGE_OPERABLE
    return FUNCTIONAL_STAGE_BANKED


def build_result(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    research: Mapping[str, Any],
    certified: Mapping[str, Any],
    operator_confirmation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage = functional_stage_for_confirmation(operator_confirmation)
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_case_result_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "subject_case": SUBJECT_CASE,
        "decision_id": DECISION_ID,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "cutoff_at": case_manifest["cutoff"]["cutoff_at"],
        "family_one_source_family_id": case_manifest["family_one"]["source_family_id"],
        "family_two_source_family_id": case_manifest["family_two"]["source_family_id"],
        "family_one_package_manifest_hash": case_manifest["family_one"][
            "package_manifest_hash"
        ],
        "family_two_package_manifest_hash": case_manifest["family_two"][
            "package_manifest_hash"
        ],
        "coverage_hash": coverage["coverage_hash"],
        "coverage_status": coverage["coverage_status"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "claim_outcome": case_claim["claim_outcome"],
        "adjudication_hash": adjudication["adjudication_hash"],
        "adjudication_kind": adjudication["adjudication_kind"],
        "research_decision_hash": research["research_decision_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "portfolio_action_invariant": True,
        "rationale_ref": research["rationale_ref"],
        "certified_decision_result_hash": certified.get(
            "certified_decision_result_hash"
        ),
        "certification_status": certified["certification"]["certification_status"],
        "shipped_product_score": SHIPPED_PRODUCT_SCORE,
        "observed_comparison_count": OBSERVED_COMPARISON_COUNT,
        "functional_stage": stage,
        "capture_surface": (
            None
            if operator_confirmation is None
            else operator_confirmation.get("capture_surface")
        ),
        "independent_source_count": 2,
        "real_external_source_packages_processed": 2,
        "data_admission_certificates_earned": 2,
        "formal_comparison_status": "DEFERRED_AFTER_ALPHA",
        "publication_authorized": False,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    body["result_hash"] = domain_hash(RESULT_DOMAIN, body)
    return body


def build_export_bundle(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    research: Mapping[str, Any],
    result: Mapping[str, Any],
    evidence_panel: Mapping[str, Any] | None = None,
    pre_adjudication_seal: Mapping[str, Any] | None = None,
    operator_confirmation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {
        "case_manifest": _plain(case_manifest),
        "coverage": _plain(coverage),
        "case_claim": _plain(case_claim),
        "adjudication": _plain(adjudication),
        "research_decision": _plain(research),
        "result": _plain(result),
    }
    if evidence_panel is not None:
        artifacts["evidence_panel"] = _plain(evidence_panel)
    if pre_adjudication_seal is not None:
        artifacts["pre_adjudication_seal"] = _plain(pre_adjudication_seal)
    if operator_confirmation is not None:
        artifacts["operator_confirmation"] = _plain(operator_confirmation)
    body: dict[str, Any] = {
        "schema_version": "gv_alpha0_case_export_v1",
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_hash": coverage["coverage_hash"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "adjudication_hash": adjudication["adjudication_hash"],
        "research_decision_hash": research["research_decision_hash"],
        "result_hash": result["result_hash"],
        "artifacts": artifacts,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if operator_confirmation is not None:
        body["operator_confirmation_hash"] = operator_confirmation[
            "operator_confirmation_hash"
        ]
    if evidence_panel is not None:
        body["evidence_panel_hash"] = evidence_panel["evidence_panel_hash"]
    if pre_adjudication_seal is not None:
        body["pre_adjudication_seal_hash"] = pre_adjudication_seal[
            "pre_adjudication_seal_hash"
        ]
    body["export_hash"] = domain_hash(EXPORT_DOMAIN, body)
    return body


def build_decision_packet_markdown(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    research: Mapping[str, Any],
    result: Mapping[str, Any],
) -> str:
    lines = [
        "# GV-ALPHA0-CLOSE — Case Decision Packet",
        "",
        f"- case_id: `{CASE_ID}`",
        f"- slice: `{SLICE_CLASSIFICATION}`",
        f"- stage: `{FUNCTIONAL_STAGE}`",
        f"- cutoff_at: `{case_manifest['cutoff']['cutoff_at']}`",
        f"- case_manifest_hash: `{case_manifest['case_manifest_hash']}`",
        f"- family_one: `{case_manifest['family_one']['source_family_id']}` "
        f"pkg=`{case_manifest['family_one']['package_manifest_hash']}`",
        f"- family_two: `{case_manifest['family_two']['source_family_id']}` "
        f"pkg=`{case_manifest['family_two']['package_manifest_hash']}`",
        f"- coverage: `{coverage['coverage_status']}` "
        f"(overlap only; not claim sufficiency) hash=`{coverage['coverage_hash']}`",
        f"- claim: `{case_claim['claim_outcome']}` hash=`{case_claim['case_claim_hash']}`",
        f"- adjudication: kind=`{adjudication['adjudication_kind']}` "
        f"label=`{adjudication['adjudicator_label']}` "
        f"trusted_identity=`{adjudication['trusted_identity']}` "
        f"discretionary=`{adjudication['discretionary_decision']}`",
        f"- research: `{research['research_action']}` → `{research['portfolio_action']}` "
        f"(invariant NO_POSITION)",
        f"- decision_id: `{DECISION_ID}`",
        f"- result_hash: `{result['result_hash']}`",
        f"- score/observed: `{SHIPPED_PRODUCT_SCORE}` / `{OBSERVED_COMPARISON_COUNT}`",
        f"- publication_authorized: `{result['publication_authorized']}`",
        "",
        "## Overlap pairs (coverage only)",
    ]
    for pair in coverage["overlap_pairs"]:
        lines.append(
            f"- `{pair['overlap_id']}` {pair['family_one_statement_id']} ↔ "
            f"{pair['family_two_fact_id']} ({pair['overlap_class']})"
        )
    lines.extend(["", "## Boundary", CLAIM_BOUNDARY, ""])
    return "\n".join(lines)


def build_case_workspace_view_model(
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    evidence_panel: Mapping[str, Any] | None = None,
    pre_adjudication_seal: Mapping[str, Any] | None = None,
    operator_confirmation: Mapping[str, Any] | None = None,
    adjudication: Mapping[str, Any] | None = None,
    result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure view model for Case Workspace (default product surface)."""

    certified = result is not None and adjudication is not None
    stage = (
        functional_stage_for_confirmation(operator_confirmation)
        if certified
        else FUNCTIONAL_STAGE_PRE_ADJUDICATION
    )
    return {
        "page": "CASE_WORKSPACE",
        "case_id": CASE_ID,
        "subject_case": SUBJECT_CASE,
        "slice_classification": SLICE_CLASSIFICATION,
        "functional_stage": stage,
        "capture_surface": (
            None
            if operator_confirmation is None
            else operator_confirmation.get("capture_surface")
        ),
        "seal_verified_on_load": False,
        "cutoff_at": case_manifest["cutoff"]["cutoff_at"],
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "family_one_id": case_manifest["family_one"]["source_family_id"],
        "family_two_id": case_manifest["family_two"]["source_family_id"],
        "coverage_status": coverage["coverage_status"],
        "coverage_meaning": coverage["coverage_meaning"],
        "overlap_count": coverage["overlap_count"],
        "overlap_panels": (
            []
            if evidence_panel is None
            else list(evidence_panel.get("overlap_panels") or [])
        ),
        "evidence_panel_hash": (
            None if evidence_panel is None else evidence_panel["evidence_panel_hash"]
        ),
        "pre_adjudication_seal_hash": (
            None
            if pre_adjudication_seal is None
            else pre_adjudication_seal["pre_adjudication_seal_hash"]
        ),
        "claim_outcome": case_claim["claim_outcome"],
        "permitted_portfolio_actions": list(PERMITTED_PORTFOLIO_ACTIONS),
        "portfolio_action_invariant": PORTFOLIO_ACTION_NO_POSITION,
        "operator_confirmation_present": operator_confirmation is not None,
        "operator_confirmation_hash": (
            None
            if operator_confirmation is None
            else operator_confirmation["operator_confirmation_hash"]
        ),
        "adjudication_kind": ADJUDICATION_KIND,
        "adjudication_present": adjudication is not None,
        "adjudication_hash": (
            None if adjudication is None else adjudication["adjudication_hash"]
        ),
        "result_hash": None if result is None else result["result_hash"],
        "certification_status": (
            None if result is None else result.get("certification_status")
        ),
        "shipped_product_score": SHIPPED_PRODUCT_SCORE,
        "observed_comparison_count": OBSERVED_COMPARISON_COUNT,
        "claim_boundary": CLAIM_BOUNDARY,
        "awaiting_operator_confirmation": not certified,
    }


def rebuild_pre_adjudication_chain(
    *,
    root: Path | None = None,
    family_pins: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Sealed pre-adjudication only — no confirmation, adjudication, or cert."""

    pins = _plain(family_pins) if family_pins is not None else load_family_pins(root=root)
    case_manifest = build_case_manifest(root=root, family_pins=pins)
    coverage = build_coverage_assessment(
        case_manifest, family_pins=pins, root=root
    )
    case_claim = build_case_claim(case_manifest, coverage)
    evidence_panel = build_evidence_panel(
        case_manifest, coverage, family_pins=pins, root=root
    )
    seal = build_pre_adjudication_seal(
        case_manifest=case_manifest,
        coverage=coverage,
        case_claim=case_claim,
        evidence_panel=evidence_panel,
    )
    return {
        "family_pins": {
            "family_one": pins["family_one"],
            "family_two": pins["family_two"],
        },
        "case_manifest": case_manifest,
        "coverage": coverage,
        "case_claim": case_claim,
        "evidence_panel": evidence_panel,
        "pre_adjudication_seal": seal,
    }


def rebuild_canonical_close_chain(
    *,
    root: Path | None = None,
    adjudicator_label: str = "SELF_LABELLED_OPERATOR",
    adjudicated_at: str = "2026-07-23T12:00:00.000000Z",
    capture_surface: str = CAPTURE_SURFACE_OFFLINE,
    confirmation_phrase: str = OPERATOR_CONFIRMATION_PHRASE,
    verifier_runner: VerifierRunner = run_isolated_verifier,
    include_certified: bool = True,
) -> dict[str, Any]:
    """Deterministic rebuild of the close case from raw family banks.

    Confirmation is always materialised before adjudication/certification.
    """

    sealed = rebuild_pre_adjudication_chain(root=root)
    case_manifest = sealed["case_manifest"]
    coverage = sealed["coverage"]
    case_claim = sealed["case_claim"]
    evidence_panel = sealed["evidence_panel"]
    pre_seal = sealed["pre_adjudication_seal"]
    confirmation = build_operator_confirmation(
        case_manifest=case_manifest,
        coverage=coverage,
        case_claim=case_claim,
        pre_adjudication_seal=pre_seal,
        adjudicator_label=adjudicator_label,
        confirmed_at=adjudicated_at,
        confirmation_phrase=confirmation_phrase,
        capture_surface=capture_surface,
    )
    adjudication = capture_case_workspace_adjudication(
        case_manifest=case_manifest,
        coverage=coverage,
        case_claim=case_claim,
        operator_confirmation=confirmation,
        adjudicator_label=adjudicator_label,
        adjudicated_at=adjudicated_at,
    )
    research = build_research_decision(
        case_manifest, coverage, case_claim, adjudication
    )
    out: dict[str, Any] = {
        "family_pins": sealed["family_pins"],
        "case_manifest": case_manifest,
        "coverage": coverage,
        "case_claim": case_claim,
        "evidence_panel": evidence_panel,
        "pre_adjudication_seal": pre_seal,
        "operator_confirmation": confirmation,
        "adjudication": adjudication,
        "research": research,
    }
    if include_certified:
        certified = _build_certified(research, verifier_runner=verifier_runner)
        result = build_result(
            case_manifest=case_manifest,
            coverage=coverage,
            case_claim=case_claim,
            adjudication=adjudication,
            research=research,
            certified=certified,
            operator_confirmation=confirmation,
        )
        export = build_export_bundle(
            case_manifest=case_manifest,
            coverage=coverage,
            case_claim=case_claim,
            adjudication=adjudication,
            research=research,
            result=result,
            evidence_panel=evidence_panel,
            pre_adjudication_seal=pre_seal,
            operator_confirmation=confirmation,
        )
        out["certified"] = certified
        out["result"] = result
        out["export"] = export
        out["decision_packet_md"] = build_decision_packet_markdown(
            case_manifest=case_manifest,
            coverage=coverage,
            case_claim=case_claim,
            adjudication=adjudication,
            research=research,
            result=result,
        )
    return out


def _exact_match(
    banked: Mapping[str, Any],
    rebuilt: Mapping[str, Any],
    *,
    error_code: str,
) -> None:
    if _canonical_json_bytes(banked) != _canonical_json_bytes(rebuilt):
        raise GvAlpha0CloseError(error_code)


def verify_close_chain(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Rebuild-from-raw + exact-compare banked close artifacts (adversarial surface)."""

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else CASE_DIR
    banked_manifest = _load_json(
        out_dir / "case_manifest.json", missing_code="ALPHA0_CLOSE_MANIFEST_MISSING"
    )
    banked_coverage = _load_json(
        out_dir / "coverage.json", missing_code="ALPHA0_CLOSE_COVERAGE_MISSING"
    )
    banked_claim = _load_json(
        out_dir / "case_claim.json", missing_code="ALPHA0_CLOSE_CLAIM_MISSING"
    )
    banked_evidence = _load_json(
        out_dir / "evidence_panel.json",
        missing_code="ALPHA0_CLOSE_EVIDENCE_PANEL_MISSING",
    )
    banked_seal = _load_json(
        out_dir / "pre_adjudication_seal.json",
        missing_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_MISSING",
    )
    banked_confirm = _load_json(
        out_dir / "operator_confirmation.json",
        missing_code="ALPHA0_CLOSE_OPERATOR_CONFIRMATION_MISSING",
    )
    banked_adj = _load_json(
        out_dir / "adjudication.json", missing_code="ALPHA0_CLOSE_ADJUDICATION_MISSING"
    )
    banked_research = _load_json(
        out_dir / "research_decision.json",
        missing_code="ALPHA0_CLOSE_RESEARCH_MISSING",
    )
    banked_result = _load_json(
        out_dir / "result.json", missing_code="ALPHA0_CLOSE_RESULT_MISSING"
    )
    banked_export = _load_json(
        out_dir / "export_bundle.json", missing_code="ALPHA0_CLOSE_EXPORT_MISSING"
    )

    rebuilt = rebuild_canonical_close_chain(
        root=base,
        adjudicator_label=str(banked_adj["adjudicator_label"]),
        adjudicated_at=str(banked_adj["adjudicated_at"]),
        capture_surface=str(banked_confirm.get("capture_surface", CAPTURE_SURFACE_OFFLINE)),
        confirmation_phrase=str(
            banked_confirm.get("confirmation_phrase", OPERATOR_CONFIRMATION_PHRASE)
        ),
        verifier_runner=verifier_runner,
        include_certified=True,
    )
    _exact_match(
        banked_manifest,
        rebuilt["case_manifest"],
        error_code="ALPHA0_CLOSE_MANIFEST_NOT_CANONICAL",
    )
    _exact_match(
        banked_coverage,
        rebuilt["coverage"],
        error_code="ALPHA0_CLOSE_COVERAGE_NOT_CANONICAL",
    )
    _exact_match(
        banked_claim,
        rebuilt["case_claim"],
        error_code="ALPHA0_CLOSE_CLAIM_NOT_CANONICAL",
    )
    _exact_match(
        banked_evidence,
        rebuilt["evidence_panel"],
        error_code="ALPHA0_CLOSE_EVIDENCE_PANEL_NOT_CANONICAL",
    )
    _exact_match(
        banked_seal,
        rebuilt["pre_adjudication_seal"],
        error_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_NOT_CANONICAL",
    )
    _exact_match(
        banked_confirm,
        rebuilt["operator_confirmation"],
        error_code="ALPHA0_CLOSE_OPERATOR_CONFIRMATION_NOT_CANONICAL",
    )
    _exact_match(
        banked_adj,
        rebuilt["adjudication"],
        error_code="ALPHA0_CLOSE_ADJUDICATION_NOT_CANONICAL",
    )
    _exact_match(
        banked_research,
        rebuilt["research"],
        error_code="ALPHA0_CLOSE_RESEARCH_NOT_CANONICAL",
    )
    _exact_match(
        banked_result, rebuilt["result"], error_code="ALPHA0_CLOSE_RESULT_NOT_CANONICAL"
    )
    _exact_match(
        banked_export,
        rebuilt["export"],
        error_code="ALPHA0_CLOSE_EXPORT_NOT_CANONICAL",
    )
    if banked_result.get("portfolio_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_RESULT_POSITION_INVARIANT_BROKEN")
    if banked_result.get("claim_outcome") != CLAIM_OUTCOME_INSUFFICIENT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_RESULT_CLAIM_INVARIANT_BROKEN")
    if banked_result.get("coverage_status") != COVERAGE_PARTIAL:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_RESULT_COVERAGE_INVARIANT_BROKEN")
    if banked_result.get("shipped_product_score") != SHIPPED_PRODUCT_SCORE:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_SCORE_DRIFT")
    if banked_result.get("observed_comparison_count") != OBSERVED_COMPARISON_COUNT:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_OBSERVED_DRIFT")
    if not banked_confirm.get("confirmed"):
        raise GvAlpha0CloseError("ALPHA0_CLOSE_CONFIRMATION_NOT_PRESENT")
    return rebuilt


def replay_export_bundle(
    export_bundle: Mapping[str, Any],
    *,
    root: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Replay: rebuild chain and require export/result hash match."""

    arts = export_bundle["artifacts"]
    adj = arts["adjudication"]
    confirm = arts.get("operator_confirmation") or {}
    rebuilt = rebuild_canonical_close_chain(
        root=root,
        adjudicator_label=str(adj["adjudicator_label"]),
        adjudicated_at=str(adj["adjudicated_at"]),
        capture_surface=str(confirm.get("capture_surface", CAPTURE_SURFACE_OFFLINE)),
        confirmation_phrase=str(
            confirm.get("confirmation_phrase", OPERATOR_CONFIRMATION_PHRASE)
        ),
        verifier_runner=verifier_runner,
        include_certified=True,
    )
    if rebuilt["result"]["result_hash"] != arts["result"]["result_hash"]:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_REPLAY_RESULT_MISMATCH")
    if rebuilt["export"]["export_hash"] != export_bundle["export_hash"]:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_REPLAY_EXPORT_MISMATCH")
    return rebuilt


def _write_close_bundle(
    out_dir: Path,
    *,
    case_manifest: Mapping[str, Any],
    coverage: Mapping[str, Any],
    case_claim: Mapping[str, Any],
    evidence_panel: Mapping[str, Any],
    pre_adjudication_seal: Mapping[str, Any],
    operator_confirmation: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    research: Mapping[str, Any],
    export: Mapping[str, Any],
    packet_md: str,
    view: Mapping[str, Any],
    result: Mapping[str, Any],
) -> None:
    _atomic_write_case_bundle(
        out_dir,
        {
            "case_manifest.json": case_manifest,
            "coverage.json": coverage,
            "case_claim.json": case_claim,
            "evidence_panel.json": evidence_panel,
            "pre_adjudication_seal.json": pre_adjudication_seal,
            "operator_confirmation.json": operator_confirmation,
            "adjudication.json": adjudication,
            "research_decision.json": research,
            "export_bundle.json": export,
            "decision_packet.md": packet_md,
            "case_workspace_view.json": view,
            "result.json": result,
        },
        promote_order=(
            "case_manifest.json",
            "coverage.json",
            "case_claim.json",
            "evidence_panel.json",
            "pre_adjudication_seal.json",
            "operator_confirmation.json",
            "adjudication.json",
            "research_decision.json",
            "export_bundle.json",
            "decision_packet.md",
            "case_workspace_view.json",
            "result.json",
        ),
    )


def seal_pre_adjudication_case(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
) -> dict[str, Any]:
    """Write sealed pre-adjudication only (offline bank tool — not page-load)."""

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else CASE_DIR
    sealed = rebuild_pre_adjudication_chain(root=base)
    view = build_case_workspace_view_model(
        case_manifest=sealed["case_manifest"],
        coverage=sealed["coverage"],
        case_claim=sealed["case_claim"],
        evidence_panel=sealed["evidence_panel"],
        pre_adjudication_seal=sealed["pre_adjudication_seal"],
    )
    _atomic_write_case_bundle(
        out_dir,
        {
            "case_manifest.json": sealed["case_manifest"],
            "coverage.json": sealed["coverage"],
            "case_claim.json": sealed["case_claim"],
            "evidence_panel.json": sealed["evidence_panel"],
            "pre_adjudication_seal.json": sealed["pre_adjudication_seal"],
            "case_workspace_view.json": view,
        },
        promote_order=(
            "case_manifest.json",
            "coverage.json",
            "case_claim.json",
            "evidence_panel.json",
            "pre_adjudication_seal.json",
            "case_workspace_view.json",
        ),
    )
    return {
        "case_id": CASE_ID,
        "functional_stage": FUNCTIONAL_STAGE_PRE_ADJUDICATION,
        "case_dir": str(out_dir),
        "pre_adjudication_seal_hash": sealed["pre_adjudication_seal"][
            "pre_adjudication_seal_hash"
        ],
        "evidence_panel_hash": sealed["evidence_panel"]["evidence_panel_hash"],
        "view": view,
    }


def confirm_operator_and_certify(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    adjudicator_label: str,
    confirmed_at: str,
    confirmation_phrase: str = OPERATOR_CONFIRMATION_PHRASE,
    capture_surface: str = CAPTURE_SURFACE_UI,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Persist operator confirmation then certify. Requires existing pre-adj seal."""

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else CASE_DIR
    banked_seal = _load_json(
        out_dir / "pre_adjudication_seal.json",
        missing_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_MISSING",
    )
    banked_manifest = _load_json(
        out_dir / "case_manifest.json", missing_code="ALPHA0_CLOSE_MANIFEST_MISSING"
    )
    banked_coverage = _load_json(
        out_dir / "coverage.json", missing_code="ALPHA0_CLOSE_COVERAGE_MISSING"
    )
    banked_claim = _load_json(
        out_dir / "case_claim.json", missing_code="ALPHA0_CLOSE_CLAIM_MISSING"
    )
    banked_evidence = _load_json(
        out_dir / "evidence_panel.json",
        missing_code="ALPHA0_CLOSE_EVIDENCE_PANEL_MISSING",
    )
    # Rebuild must match banked seal (no silent authority rewrite).
    rebuilt_seal = rebuild_pre_adjudication_chain(root=base)
    _exact_match(
        banked_manifest,
        rebuilt_seal["case_manifest"],
        error_code="ALPHA0_CLOSE_MANIFEST_NOT_CANONICAL",
    )
    _exact_match(
        banked_coverage,
        rebuilt_seal["coverage"],
        error_code="ALPHA0_CLOSE_COVERAGE_NOT_CANONICAL",
    )
    _exact_match(
        banked_claim,
        rebuilt_seal["case_claim"],
        error_code="ALPHA0_CLOSE_CLAIM_NOT_CANONICAL",
    )
    _exact_match(
        banked_evidence,
        rebuilt_seal["evidence_panel"],
        error_code="ALPHA0_CLOSE_EVIDENCE_PANEL_NOT_CANONICAL",
    )
    _exact_match(
        banked_seal,
        rebuilt_seal["pre_adjudication_seal"],
        error_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_NOT_CANONICAL",
    )

    confirmation = build_operator_confirmation(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        pre_adjudication_seal=banked_seal,
        adjudicator_label=adjudicator_label,
        confirmed_at=confirmed_at,
        confirmation_phrase=confirmation_phrase,
        capture_surface=capture_surface,
    )
    adjudication = capture_case_workspace_adjudication(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        operator_confirmation=confirmation,
    )
    research = build_research_decision(
        banked_manifest, banked_coverage, banked_claim, adjudication
    )
    certified = _build_certified(research, verifier_runner=verifier_runner)
    result = build_result(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        adjudication=adjudication,
        research=research,
        certified=certified,
        operator_confirmation=confirmation,
    )
    export = build_export_bundle(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        adjudication=adjudication,
        research=research,
        result=result,
        evidence_panel=banked_evidence,
        pre_adjudication_seal=banked_seal,
        operator_confirmation=confirmation,
    )

    packet_md = build_decision_packet_markdown(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        adjudication=adjudication,
        research=research,
        result=result,
    )
    view = build_case_workspace_view_model(
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        evidence_panel=banked_evidence,
        pre_adjudication_seal=banked_seal,
        operator_confirmation=confirmation,
        adjudication=adjudication,
        result=result,
    )
    _write_close_bundle(
        out_dir,
        case_manifest=banked_manifest,
        coverage=banked_coverage,
        case_claim=banked_claim,
        evidence_panel=banked_evidence,
        pre_adjudication_seal=banked_seal,
        operator_confirmation=confirmation,
        adjudication=adjudication,
        research=research,
        export=export,
        packet_md=packet_md,
        view=view,
        result=result,
    )
    return {
        "case_id": CASE_ID,
        "functional_stage": result["functional_stage"],
        "operator_confirmation_hash": confirmation["operator_confirmation_hash"],
        "adjudication_hash": adjudication["adjudication_hash"],
        "certification_status": result["certification_status"],
        "result_hash": result["result_hash"],
        "export_hash": export["export_hash"],
        "case_dir": str(out_dir),
        "view": view,
        "published": False,
        "publication_authorized": False,
    }


def run_v2_alpha0_case_close(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    adjudicator_label: str = "SELF_LABELLED_OPERATOR",
    adjudicated_at: str = "2026-07-23T12:00:00.000000Z",
    capture_surface: str = CAPTURE_SURFACE_OFFLINE,
    publish: bool = False,
    current_target: Path | None = None,
    current_lock: Path | None = None,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Run the close vertical. publish defaults False (post-dogfood only).

    Offline bank tool path: materialises confirmation then certifies.
    Product UI must call seal_pre_adjudication_case (offline) +
    confirm_operator_and_certify (explicit action) — never auto-build on load.
    """

    if publish:
        # Explicit gate: publication is a later car after fresh-clone/dogfood.
        raise GvAlpha0CloseError(
            "ALPHA0_CLOSE_PUBLICATION_NOT_YET_AUTHORIZED:"
            "publish only after raw rebuild + adversarial + fresh-clone/dogfood"
        )

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else CASE_DIR
    chain = rebuild_canonical_close_chain(
        root=base,
        adjudicator_label=adjudicator_label,
        adjudicated_at=adjudicated_at,
        capture_surface=capture_surface,
        verifier_runner=verifier_runner,
        include_certified=True,
    )
    case_manifest = chain["case_manifest"]
    coverage = chain["coverage"]
    case_claim = chain["case_claim"]
    evidence_panel = chain["evidence_panel"]
    pre_seal = chain["pre_adjudication_seal"]
    confirmation = chain["operator_confirmation"]
    adjudication = chain["adjudication"]
    research = chain["research"]
    certified = chain["certified"]
    result = chain["result"]
    export = chain["export"]
    packet_md = chain["decision_packet_md"]
    view = build_case_workspace_view_model(
        case_manifest=case_manifest,
        coverage=coverage,
        case_claim=case_claim,
        evidence_panel=evidence_panel,
        pre_adjudication_seal=pre_seal,
        operator_confirmation=confirmation,
        adjudication=adjudication,
        result=result,
    )

    _write_close_bundle(
        out_dir,
        case_manifest=case_manifest,
        coverage=coverage,
        case_claim=case_claim,
        evidence_panel=evidence_panel,
        pre_adjudication_seal=pre_seal,
        operator_confirmation=confirmation,
        adjudication=adjudication,
        research=research,
        export=export,
        packet_md=packet_md,
        view=view,
        result=result,
    )

    publication: CurrentDecisionPublicationResult | None = None
    _ = (publish, current_target, current_lock, publication, certified)

    return {
        "case_id": CASE_ID,
        "slice_classification": SLICE_CLASSIFICATION,
        "decision_id": DECISION_ID,
        "case_manifest_hash": case_manifest["case_manifest_hash"],
        "coverage_status": coverage["coverage_status"],
        "coverage_hash": coverage["coverage_hash"],
        "claim_outcome": case_claim["claim_outcome"],
        "case_claim_hash": case_claim["case_claim_hash"],
        "operator_confirmation_hash": confirmation["operator_confirmation_hash"],
        "adjudication_hash": adjudication["adjudication_hash"],
        "research_action": research["research_action"],
        "portfolio_action": research["portfolio_action"],
        "certification_status": result["certification_status"],
        "result_hash": result["result_hash"],
        "export_hash": export["export_hash"],
        "shipped_product_score": result["shipped_product_score"],
        "observed_comparison_count": result["observed_comparison_count"],
        "functional_stage": result["functional_stage"],
        "publication_authorized": result["publication_authorized"],
        "published": False,
        "case_dir": str(out_dir),
        "view": view,
    }


def load_banked_case_workspace(
    *,
    root: Path | None = None,
    case_dir: Path | None = None,
    verify: bool = True,
    verifier_runner: VerifierRunner = run_isolated_verifier,
    allow_pre_adjudication: bool = True,
) -> dict[str, Any]:
    """Load banked case for Case Workspace. Never builds authority on load.

    Product bank is sealed-only until dogfood confirmation. verify=True rebuilds
    from raw and exact-matches banked seal artifacts before returning.
    """

    base = Path(root) if root is not None else ROOT
    out_dir = Path(case_dir) if case_dir is not None else (base / CASE_DIR.relative_to(ROOT))
    result_path = out_dir / "result.json"
    seal_path = out_dir / "pre_adjudication_seal.json"
    if not seal_path.is_file() and not (out_dir / "case_manifest.json").is_file():
        raise GvAlpha0CloseError(
            "ALPHA0_CLOSE_CASE_BANK_MISSING:"
            "seal offline via seal_pre_adjudication_case; "
            "page load never auto-builds; product bank is sealed-only pre-dogfood"
        )

    if result_path.is_file():
        if verify:
            verify_close_chain(
                root=base, case_dir=out_dir, verifier_runner=verifier_runner
            )
        # Prefer live model rebuild over stale view JSON so stage/capture_surface
        # and seal_verified_on_load stay accurate.
        manifest = _load_json(
            out_dir / "case_manifest.json", missing_code="ALPHA0_CLOSE_MANIFEST_MISSING"
        )
        coverage = _load_json(
            out_dir / "coverage.json", missing_code="ALPHA0_CLOSE_COVERAGE_MISSING"
        )
        claim = _load_json(
            out_dir / "case_claim.json", missing_code="ALPHA0_CLOSE_CLAIM_MISSING"
        )
        evidence = _load_json(
            out_dir / "evidence_panel.json",
            missing_code="ALPHA0_CLOSE_EVIDENCE_PANEL_MISSING",
        )
        seal = _load_json(
            out_dir / "pre_adjudication_seal.json",
            missing_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_MISSING",
        )
        confirm = _load_json(
            out_dir / "operator_confirmation.json",
            missing_code="ALPHA0_CLOSE_OPERATOR_CONFIRMATION_MISSING",
        )
        adj = _load_json(
            out_dir / "adjudication.json",
            missing_code="ALPHA0_CLOSE_ADJUDICATION_MISSING",
        )
        result = _load_json(
            out_dir / "result.json", missing_code="ALPHA0_CLOSE_RESULT_MISSING"
        )
        model = build_case_workspace_view_model(
            case_manifest=manifest,
            coverage=coverage,
            case_claim=claim,
            evidence_panel=evidence,
            pre_adjudication_seal=seal,
            operator_confirmation=confirm,
            adjudication=adj,
            result=result,
        )
        model["seal_verified_on_load"] = bool(verify)
        return model

    if not allow_pre_adjudication:
        raise GvAlpha0CloseError("ALPHA0_CLOSE_RESULT_MISSING")
    # Pre-adjudication sealed surface (awaiting explicit operator confirmation).
    if verify:
        rebuilt = rebuild_pre_adjudication_chain(root=base)
        for name, key, code in (
            ("case_manifest.json", "case_manifest", "ALPHA0_CLOSE_MANIFEST_NOT_CANONICAL"),
            ("coverage.json", "coverage", "ALPHA0_CLOSE_COVERAGE_NOT_CANONICAL"),
            ("case_claim.json", "case_claim", "ALPHA0_CLOSE_CLAIM_NOT_CANONICAL"),
            (
                "evidence_panel.json",
                "evidence_panel",
                "ALPHA0_CLOSE_EVIDENCE_PANEL_NOT_CANONICAL",
            ),
            (
                "pre_adjudication_seal.json",
                "pre_adjudication_seal",
                "ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_NOT_CANONICAL",
            ),
        ):
            banked = _load_json(
                out_dir / name, missing_code=f"ALPHA0_CLOSE_{key.upper()}_MISSING"
            )
            _exact_match(banked, rebuilt[key], error_code=code)
    elif not seal_path.is_file():
        raise GvAlpha0CloseError("ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_MISSING")
    manifest = _load_json(
        out_dir / "case_manifest.json", missing_code="ALPHA0_CLOSE_MANIFEST_MISSING"
    )
    coverage = _load_json(
        out_dir / "coverage.json", missing_code="ALPHA0_CLOSE_COVERAGE_MISSING"
    )
    claim = _load_json(
        out_dir / "case_claim.json", missing_code="ALPHA0_CLOSE_CLAIM_MISSING"
    )
    evidence = _load_json(
        out_dir / "evidence_panel.json",
        missing_code="ALPHA0_CLOSE_EVIDENCE_PANEL_MISSING",
    )
    seal = _load_json(
        out_dir / "pre_adjudication_seal.json",
        missing_code="ALPHA0_CLOSE_PRE_ADJUDICATION_SEAL_MISSING",
    )
    model = build_case_workspace_view_model(
        case_manifest=manifest,
        coverage=coverage,
        case_claim=claim,
        evidence_panel=evidence,
        pre_adjudication_seal=seal,
    )
    model["seal_verified_on_load"] = bool(verify)
    return model


if __name__ == "__main__":
    out = run_v2_alpha0_case_close(publish=False)
    print(json.dumps({k: out[k] for k in out if k != "view"}, indent=2, sort_keys=True))
