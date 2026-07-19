"""GV-E0B-DV1 Contradiction Case (G08): observed within-case decision comparison.

One-case product path after banked E0A substrate. G08 evidence remains a
synthetic adversarial fixture. Human baseline and post-packet decisions must be
externally authored; rubric scores must be authored by a different reviewer.

Hardcoded baseline/post/rubric outcomes are prohibited. Positive, zero, or
negative rubric deltas are all protocol-valid. E0B product close requires real
human operator records (same operator for baseline and post) plus an independent
human reviewer for the rubric. Engine test fixtures validate machinery only and
never count as an observed comparison.

Endpoint authority: docs/architecture/godview_e0/e0_acceptance_tests.md G08.
Frozen endpoint: observed within-case difference only; no causal/general claim.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Any

from core.gv_fs0_book import (
    DecisionEnvelope,
    OpenBookBuild,
    _build_book,
    _build_decision,
    build_no_position_source_fixture,
)
from core.gv_fs0_canonical import (
    CANONICAL_TIMESTAMP_RE,
    SHA256_RE,
    canonical_document_bytes,
    domain_hash,
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
DEFAULT_CASE_DIR = ROOT / "data" / "gv_e0b" / "dv1_g08"
DEFAULT_RESULT_JSON = DEFAULT_CASE_DIR / "result.json"
DEFAULT_DECISION_PACKET_MD = DEFAULT_CASE_DIR / "decision_packet.md"
DEFAULT_BASELINE_PATH = DEFAULT_CASE_DIR / "captures" / "baseline_seal.json"
DEFAULT_POST_PATH = DEFAULT_CASE_DIR / "captures" / "post_packet_seal.json"
DEFAULT_RUBRIC_PATH = DEFAULT_CASE_DIR / "captures" / "rubric_scores.json"

CASE_ID = "E0B_DV1_G08_CONTRADICTION_1"
PROTOCOL_ID = "GODVIEW-E0-P0-V1"
MODULE = "G_supply"
SUBJECT = "SYNTH_MU_SUPPLY"
BLOCK_REASON = "CONTRADICTORY_INDISPENSABLE_EVIDENCE"
RUN_STATE_BLOCKED = "BLOCKED"
RUN_CLASS_SYNTHETIC = "SYNTHETIC_DEV_RUN"
RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"
E0B_DECISION_ID = "DECISION_E0B_DV1_G08_1"
RATIONALE_REF_PREFIX = "E0B:CMP:"

DOMAIN_BUNDLE = "GV-E0B:DV1:BUNDLE:V1"
DOMAIN_BASELINE = "GV-E0B:DV1:BASELINE:V1"
DOMAIN_PACKET = "GV-E0B:DV1:PACKET:V1"
DOMAIN_POST = "GV-E0B:DV1:POST_PACKET:V1"
DOMAIN_RUBRIC = "GV-E0B:DV1:RUBRIC:V1"
DOMAIN_COMPARISON = "GV-E0B:DV1:COMPARISON:V1"
DOMAIN_RESULT = "GV-E0B:DV1:RESULT:V1"

AUTH_FIXTURE = "ENGINE_TEST_FIXTURE"
AUTH_REAL_OPERATOR = "REAL_HUMAN_OPERATOR"
AUTH_REAL_REVIEWER = "REAL_HUMAN_REVIEWER"

RUBRIC_ITEMS: tuple[str, ...] = (
    "selected_action_defensibility",
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
    "supply_demand_business_shareholder_valuation_claim_separation",
    "avoidance_of_claims_beyond_evidence",
    "rationale_traceability",
)

ALLOWED_ACTIONS = frozenset(
    {
        "ADVANCE_TO_FULL_RESEARCH",
        "HOLD_FOR_EVIDENCE",
        "REJECT_THESIS",
    }
)


class GvE0bDv1Error(RuntimeError):
    """Fail-closed E0B-DV1 contradiction-case error."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _require_mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise GvE0bDv1Error(code)
    return {str(k): v for k, v in value.items()}


def _require_str(record: Mapping[str, Any], key: str, code: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise GvE0bDv1Error(code)
    return value


def _require_bool(record: Mapping[str, Any], key: str, expected: bool, code: str) -> bool:
    value = record.get(key)
    if value is not expected:
        raise GvE0bDv1Error(code)
    return bool(value)


def _require_timestamp(record: Mapping[str, Any], key: str, code: str) -> str:
    value = _require_str(record, key, code)
    if not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error(code)
    return value


def _require_sha256(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise GvE0bDv1Error(code)
    return value


def _without_keys(record: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    banned = set(keys)
    return {k: _plain(v) for k, v in record.items() if k not in banned}


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GvE0bDv1Error(f"E0B_PATH_MISSING:{path.name}")
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GvE0bDv1Error(f"E0B_PATH_INVALID_JSON:{path.name}") from exc
    return _require_mapping(data, f"E0B_PATH_NOT_OBJECT:{path.name}")


def _atomic_write_bytes(target: Path, payload: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    temp_path = Path(raw_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def sealed_adversarial_bundle() -> Mapping[str, Any]:
    """Synthetic G08 fixture: two indispensable sources contradict on one fact."""

    body = {
        "case_id": CASE_ID,
        "protocol_id": PROTOCOL_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "decision_timestamp": "2026-07-19T12:00:00.000000Z",
        "information_cutoff": "2026-07-19T12:00:00.000000Z",
        "run_class": RUN_CLASS_SYNTHETIC,
        "indispensable_claims": [
            {
                "source_id": "SRC_A_FAB_UTIL_SYNTH",
                "indispensable": True,
                "claim_family": "C1_PHYSICAL_RELIEF_SLOWER",
                "fact_key": "qualified_sellable_supply_relief_quarters",
                "value": 8,
                "direction": "SLOWER_RELIEF",
                "statement": (
                    "Synthetic fab-utilization note: qualified sellable supply "
                    "relief requires eight quarters."
                ),
            },
            {
                "source_id": "SRC_B_CAPEX_RAMP_SYNTH",
                "indispensable": True,
                "claim_family": "C1_PHYSICAL_RELIEF_SLOWER",
                "fact_key": "qualified_sellable_supply_relief_quarters",
                "value": 2,
                "direction": "FASTER_RELIEF",
                "statement": (
                    "Synthetic capex-ramp note: qualified sellable supply relief "
                    "completes in two quarters."
                ),
            },
        ],
        "engine_prohibitions": [
            "average_contradictory_indispensable_values",
            "majority_vote_contradictory_indispensable_values",
            "provider_or_network_access",
            "full_valuation_lattice",
            "hardcoded_human_baseline_or_rubric",
        ],
    }
    digest = domain_hash(DOMAIN_BUNDLE, body)
    out = dict(body)
    out["bundle_hash"] = digest
    return _freeze(out)


def verify_bundle_seal(bundle: Mapping[str, Any]) -> str:
    """Recompute bundle hash; reject modified evidence under a claimed hash."""

    plain = _plain(bundle)
    claimed = _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
    body = _without_keys(plain, "bundle_hash")
    recomputed = domain_hash(DOMAIN_BUNDLE, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_BUNDLE_SEAL_MISMATCH")
    return recomputed


def _find_indispensable_contradictions(
    claims: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[str, list[Mapping[str, Any]]] = {}
    for claim in claims:
        if not claim.get("indispensable"):
            continue
        key = str(claim.get("fact_key") or "")
        by_key.setdefault(key, []).append(claim)
    contradictions: list[dict[str, Any]] = []
    for fact_key, group in sorted(by_key.items()):
        values = {item.get("value") for item in group}
        directions = {item.get("direction") for item in group}
        if len(values) > 1 or len(directions) > 1:
            contradictions.append(
                {
                    "fact_key": fact_key,
                    "source_ids": [str(item.get("source_id")) for item in group],
                    "values": sorted(values, key=lambda v: str(v)),
                    "directions": sorted(str(d) for d in directions),
                    "resolution": "BLOCK_NO_AVERAGE_NO_MAJORITY",
                }
            )
    return contradictions


def build_godview_packet(*, bundle: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    """Deterministic G08 packet: BLOCKED on contradictory indispensable evidence."""

    b_plain = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(b_plain)
    claims = list(b_plain.get("indispensable_claims") or [])
    if not claims:
        raise GvE0bDv1Error("E0B_BUNDLE_CLAIMS_REQUIRED")
    contradictions = _find_indispensable_contradictions(claims)
    if not contradictions:
        raise GvE0bDv1Error("E0B_G08_EXPECTS_CONTRADICTION")

    body = {
        "case_id": CASE_ID,
        "arm": "GODVIEW_PACKET",
        "bundle_hash": b_plain["bundle_hash"],
        "generated_at": "2026-07-19T12:30:00.000000Z",
        "run_state": RUN_STATE_BLOCKED,
        "block_reason": BLOCK_REASON,
        "acceptance_case": "G08",
        "run_class": RUN_CLASS_SYNTHETIC,
        "research_action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "candidate": "NONE",
        "contradictions": contradictions,
        "engine_may_not_average": True,
        "engine_may_not_majority_vote": True,
        "missing_evidence": [],
        "falsifiers": [
            {
                "falsifier_id": "F_G08_INDISPENSABLE_CONTRADICTION",
                "fact_key": item["fact_key"],
                "source_ids": item["source_ids"],
            }
            for item in contradictions
        ],
        "alpha_claim": False,
        "rationale": (
            "Indispensable sources contradict on qualified sellable supply relief "
            "quarters (8 vs 2). Engine blocks without averaging or majority vote."
        ),
    }
    digest = domain_hash(DOMAIN_PACKET, body)
    out = dict(body)
    out["packet_hash"] = digest
    return _freeze(out)


def verify_packet_seal(packet: Mapping[str, Any]) -> str:
    plain = _plain(packet)
    claimed = _require_sha256(plain.get("packet_hash"), "E0B_PACKET_HASH_INVALID")
    body = _without_keys(plain, "packet_hash")
    recomputed = domain_hash(DOMAIN_PACKET, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_PACKET_SEAL_MISMATCH")
    return recomputed


def _validate_decision_arm(
    record: Mapping[str, Any],
    *,
    expected_arm: str,
    allowed_auth: frozenset[str],
) -> dict[str, Any]:
    plain = _require_mapping(record, "E0B_DECISION_RECORD_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    if plain.get("arm") != expected_arm:
        raise GvE0bDv1Error("E0B_ARM_MISMATCH")
    auth = _require_str(plain, "authorship_kind", "E0B_AUTHORSHIP_REQUIRED")
    if auth not in allowed_auth:
        raise GvE0bDv1Error("E0B_AUTHORSHIP_INVALID")
    operator_id = _require_str(plain, "operator_id", "E0B_OPERATOR_REQUIRED")
    sealed_at = _require_timestamp(plain, "sealed_at", "E0B_SEALED_AT_INVALID")
    bundle_hash = _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
    minutes = plain.get("human_analysis_time_minutes")
    if minutes != 60:
        raise GvE0bDv1Error("E0B_UNEQUAL_BUDGET")
    _require_bool(plain, "equal_budget_attestation", True, "E0B_EQUAL_BUDGET_REQUIRED")
    _require_bool(
        plain, "outside_research_attestation", False, "E0B_OUTSIDE_RESEARCH_FORBIDDEN"
    )
    _require_bool(
        plain,
        "post_cutoff_information_attestation",
        False,
        "E0B_POST_CUTOFF_FORBIDDEN",
    )
    action = _require_str(plain, "action", "E0B_ACTION_REQUIRED")
    if action not in ALLOWED_ACTIONS:
        raise GvE0bDv1Error("E0B_ACTION_INVALID")
    rationale = _require_str(plain, "rationale", "E0B_RATIONALE_REQUIRED")
    if plain.get("alpha_claim") is not False:
        raise GvE0bDv1Error("E0B_ALPHA_CLAIM_FORBIDDEN")
    for key in ("missing_evidence", "falsifiers", "contradictions_recognized"):
        if not isinstance(plain.get(key), list):
            raise GvE0bDv1Error(f"E0B_{key.upper()}_REQUIRED")
    return {
        "case_id": CASE_ID,
        "arm": expected_arm,
        "authorship_kind": auth,
        "operator_id": operator_id,
        "sealed_at": sealed_at,
        "bundle_hash": bundle_hash,
        "human_analysis_time_minutes": 60,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "action": action,
        "rationale": rationale,
        "missing_evidence": list(plain["missing_evidence"]),
        "falsifiers": list(plain["falsifiers"]),
        "contradictions_recognized": list(plain["contradictions_recognized"]),
        "alpha_claim": False,
    }


def seal_baseline_record(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and attach baseline_hash for an externally authored baseline."""

    body = _validate_decision_arm(
        record,
        expected_arm="HUMAN_BASELINE",
        allowed_auth=frozenset({AUTH_FIXTURE, AUTH_REAL_OPERATOR}),
    )
    if "sealed_before_packet" in record and record["sealed_before_packet"] is not True:
        raise GvE0bDv1Error("E0B_BASELINE_MUST_PREDATE_PACKET_FLAG")
    body["sealed_before_packet"] = True
    digest = domain_hash(DOMAIN_BASELINE, body)
    out = dict(body)
    out["baseline_hash"] = digest
    return _freeze(out)


def verify_baseline_seal(baseline: Mapping[str, Any]) -> str:
    plain = _plain(baseline)
    claimed = _require_sha256(plain.get("baseline_hash"), "E0B_BASELINE_HASH_INVALID")
    body = _without_keys(plain, "baseline_hash")
    # Re-validate fields after stripping hash.
    sealed = seal_baseline_record(body)
    if sealed["baseline_hash"] != claimed:
        raise GvE0bDv1Error("E0B_BASELINE_SEAL_MISMATCH")
    return claimed


def load_baseline_seal(
    path: Path,
    *,
    expected_bundle_hash: str,
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    # Accept either sealed or unsealed authoring payload.
    if "baseline_hash" in raw:
        verify_baseline_seal(raw)
        sealed = _freeze(_plain(raw))
    else:
        sealed = seal_baseline_record(raw)
    if sealed["bundle_hash"] != expected_bundle_hash:
        raise GvE0bDv1Error("E0B_BASELINE_BUNDLE_MISMATCH")
    return sealed


def seal_post_packet_record(
    record: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate and attach post_packet_hash for an externally authored post decision."""

    p = _plain(packet)
    b = _plain(baseline)
    verify_packet_seal(p)
    verify_baseline_seal(b)
    body = _validate_decision_arm(
        record,
        expected_arm="HUMAN_POST_PACKET",
        allowed_auth=frozenset({AUTH_FIXTURE, AUTH_REAL_OPERATOR}),
    )
    packet_hash = _require_sha256(p.get("packet_hash"), "E0B_PACKET_HASH_INVALID")
    claimed_packet = record.get("packet_hash")
    if claimed_packet is not None and claimed_packet != packet_hash:
        raise GvE0bDv1Error("E0B_POST_PACKET_HASH_MISMATCH")
    claimed_baseline = record.get("baseline_hash")
    if claimed_baseline is not None and claimed_baseline != b["baseline_hash"]:
        raise GvE0bDv1Error("E0B_POST_BASELINE_HASH_MISMATCH")
    if body["bundle_hash"] != b["bundle_hash"] or body["bundle_hash"] != p["bundle_hash"]:
        raise GvE0bDv1Error("E0B_POST_BUNDLE_MISMATCH")
    if body["operator_id"] != b["operator_id"]:
        raise GvE0bDv1Error("E0B_POST_OPERATOR_MUST_MATCH_BASELINE")
    if body["authorship_kind"] != b["authorship_kind"]:
        raise GvE0bDv1Error("E0B_POST_AUTHORSHIP_KIND_MISMATCH")
    # Ordering: baseline sealed_at < packet.generated_at <= post.sealed_at
    if not (b["sealed_at"] < p["generated_at"] <= body["sealed_at"]):
        raise GvE0bDv1Error("E0B_INVALID_BASELINE_SEAL_ORDERING")
    portfolio_action = record.get("portfolio_action", PORTFOLIO_ACTION_NO_POSITION)
    if portfolio_action != PORTFOLIO_ACTION_NO_POSITION:
        raise GvE0bDv1Error("E0B_PORTFOLIO_ACTION_MUST_BE_NO_POSITION")
    body["packet_hash"] = packet_hash
    body["baseline_hash"] = b["baseline_hash"]
    body["portfolio_action"] = PORTFOLIO_ACTION_NO_POSITION
    digest = domain_hash(DOMAIN_POST, body)
    out = dict(body)
    out["post_packet_hash"] = digest
    return _freeze(out)


def verify_post_packet_seal(
    post: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> str:
    plain = _plain(post)
    claimed = _require_sha256(plain.get("post_packet_hash"), "E0B_POST_HASH_INVALID")
    body = _without_keys(plain, "post_packet_hash")
    sealed = seal_post_packet_record(body, packet=packet, baseline=baseline)
    if sealed["post_packet_hash"] != claimed:
        raise GvE0bDv1Error("E0B_POST_SEAL_MISMATCH")
    return claimed


def load_post_packet_seal(
    path: Path,
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "post_packet_hash" in raw:
        verify_post_packet_seal(raw, packet=packet, baseline=baseline)
        return _freeze(_plain(raw))
    return seal_post_packet_record(raw, packet=packet, baseline=baseline)


def _validate_rubric_arm_scores(scores: Any, code: str) -> dict[str, dict[str, Any]]:
    mapping = _require_mapping(scores, code)
    if set(mapping) != set(RUBRIC_ITEMS):
        raise GvE0bDv1Error("E0B_RUBRIC_ITEMS_INVALID")
    out: dict[str, dict[str, Any]] = {}
    for item in RUBRIC_ITEMS:
        entry = _require_mapping(mapping[item], f"E0B_RUBRIC_ITEM_INVALID:{item}")
        score = entry.get("score")
        if score not in (0, 1, 2):
            raise GvE0bDv1Error(f"E0B_RUBRIC_SCORE_INVALID:{item}")
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise GvE0bDv1Error(f"E0B_RUBRIC_REASON_REQUIRED:{item}")
        out[item] = {"score": int(score), "reason": reason.strip()}
    return out


def seal_rubric_record(
    record: Mapping[str, Any],
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate separately authored rubric scores for both arms."""

    b = _plain(baseline)
    p = _plain(post)
    pkt = _plain(packet)
    verify_baseline_seal(b)
    verify_post_packet_seal(p, packet=pkt, baseline=b)
    plain = _require_mapping(record, "E0B_RUBRIC_RECORD_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    auth = _require_str(plain, "authorship_kind", "E0B_RUBRIC_AUTHORSHIP_REQUIRED")
    if auth not in {AUTH_FIXTURE, AUTH_REAL_REVIEWER}:
        raise GvE0bDv1Error("E0B_RUBRIC_AUTHORSHIP_INVALID")
    reviewer_id = _require_str(plain, "reviewer_id", "E0B_REVIEWER_REQUIRED")
    if reviewer_id == b["operator_id"]:
        raise GvE0bDv1Error("E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR")
    # Real close path: reviewer must be real if operator is real; fixtures may pair.
    if b["authorship_kind"] == AUTH_REAL_OPERATOR and auth != AUTH_REAL_REVIEWER:
        raise GvE0bDv1Error("E0B_REAL_OPERATOR_REQUIRES_REAL_REVIEWER")
    if b["authorship_kind"] == AUTH_FIXTURE and auth != AUTH_FIXTURE:
        raise GvE0bDv1Error("E0B_FIXTURE_OPERATOR_REQUIRES_FIXTURE_REVIEWER")
    scored_at = _require_timestamp(plain, "scored_at", "E0B_RUBRIC_SCORED_AT_INVALID")
    if scored_at < p["sealed_at"]:
        raise GvE0bDv1Error("E0B_RUBRIC_BEFORE_POST_FORBIDDEN")
    baseline_scores = _validate_rubric_arm_scores(
        plain.get("baseline_scores"), "E0B_BASELINE_SCORES_REQUIRED"
    )
    post_scores = _validate_rubric_arm_scores(
        plain.get("post_scores"), "E0B_POST_SCORES_REQUIRED"
    )
    body = {
        "case_id": CASE_ID,
        "authorship_kind": auth,
        "reviewer_id": reviewer_id,
        "scored_at": scored_at,
        "bundle_hash": b["bundle_hash"],
        "baseline_hash": b["baseline_hash"],
        "packet_hash": pkt["packet_hash"],
        "post_packet_hash": p["post_packet_hash"],
        "baseline_scores": baseline_scores,
        "post_scores": post_scores,
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
    }
    digest = domain_hash(DOMAIN_RUBRIC, body)
    out = dict(body)
    out["rubric_hash"] = digest
    return _freeze(out)


def verify_rubric_seal(
    rubric: Mapping[str, Any],
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> str:
    plain = _plain(rubric)
    claimed = _require_sha256(plain.get("rubric_hash"), "E0B_RUBRIC_HASH_INVALID")
    body = _without_keys(plain, "rubric_hash")
    sealed = seal_rubric_record(body, baseline=baseline, post=post, packet=packet)
    if sealed["rubric_hash"] != claimed:
        raise GvE0bDv1Error("E0B_RUBRIC_SEAL_MISMATCH")
    return claimed


def load_rubric_scores(
    path: Path,
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "rubric_hash" in raw:
        verify_rubric_seal(raw, baseline=baseline, post=post, packet=packet)
        return _freeze(_plain(raw))
    return seal_rubric_record(raw, baseline=baseline, post=post, packet=packet)


def score_totals(arm_scores: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    items = {item: int(arm_scores[item]["score"]) for item in RUBRIC_ITEMS}
    return {
        "items": items,
        "total": sum(items.values()),
        "max_total": 2 * len(RUBRIC_ITEMS),
    }


def is_observed_comparison_eligible(
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> bool:
    """True only for real human operator + independent real reviewer."""

    return (
        baseline.get("authorship_kind") == AUTH_REAL_OPERATOR
        and post.get("authorship_kind") == AUTH_REAL_OPERATOR
        and baseline.get("operator_id") == post.get("operator_id")
        and rubric.get("authorship_kind") == AUTH_REAL_REVIEWER
        and rubric.get("reviewer_id") != baseline.get("operator_id")
    )


def build_comparison(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    bundle: Mapping[str, Any] | None = None,
    packet: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Assemble comparison from external seals; never invent outcomes."""

    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    pkt = (
        _plain(packet)
        if packet is not None
        else _plain(build_godview_packet(bundle=bndl))
    )
    verify_packet_seal(pkt)
    if pkt["bundle_hash"] != bndl["bundle_hash"]:
        raise GvE0bDv1Error("E0B_PACKET_BUNDLE_MISMATCH")

    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    # Baseline must predate packet generation (G17).
    if not (baseline["sealed_at"] < pkt["generated_at"]):
        raise GvE0bDv1Error("E0B_INVALID_BASELINE_SEAL")
    post = load_post_packet_seal(post_path, packet=pkt, baseline=baseline)
    rubric = load_rubric_scores(
        rubric_path, baseline=baseline, post=post, packet=pkt
    )

    baseline_totals = score_totals(rubric["baseline_scores"])
    post_totals = score_totals(rubric["post_scores"])
    # Canonical JSON forbids negative integers; encode signed deltas as magnitude + sign.
    item_deltas: dict[str, dict[str, Any]] = {}
    for item in RUBRIC_ITEMS:
        raw = int(post_totals["items"][item]) - int(baseline_totals["items"][item])
        item_deltas[item] = {
            "magnitude": abs(raw),
            "is_negative": raw < 0,
            "value_string": str(raw),
        }
    total_raw = int(post_totals["total"]) - int(baseline_totals["total"])
    total_delta = {
        "magnitude": abs(total_raw),
        "is_negative": total_raw < 0,
        "value_string": str(total_raw),
    }
    observed_eligible = is_observed_comparison_eligible(baseline, post, rubric)

    comparison = _plain(
        {
            "case_id": CASE_ID,
            "acceptance_case": "G08",
            "run_class": RUN_CLASS_SYNTHETIC,
            "stage_claim": {
                "shipped_product_score": 39,
                "score_frozen": True,
                "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
                "target_stage": "ONE_CASE_DECISION_DELTA_OBSERVED",
                "observed_comparison_count": 1 if observed_eligible else 0,
                "e0b_close_eligible": observed_eligible,
                "alpha_claim": False,
                "general_effectiveness_claim": False,
                "causal_superiority_claim": False,
            },
            "bundle_hash": bndl["bundle_hash"],
            "baseline_hash": baseline["baseline_hash"],
            "packet_hash": pkt["packet_hash"],
            "post_packet_hash": post["post_packet_hash"],
            "rubric_hash": rubric["rubric_hash"],
            "baseline": {
                "authorship_kind": baseline["authorship_kind"],
                "operator_id": baseline["operator_id"],
                "sealed_at": baseline["sealed_at"],
                "action": baseline["action"],
                "rationale": baseline["rationale"],
                "missing_evidence": list(baseline["missing_evidence"]),
                "falsifiers": list(baseline["falsifiers"]),
                "contradictions_recognized": list(
                    baseline["contradictions_recognized"]
                ),
            },
            "godview_packet": {
                "run_state": pkt["run_state"],
                "block_reason": pkt["block_reason"],
                "research_action": pkt["research_action"],
                "generated_at": pkt["generated_at"],
                "rationale": pkt["rationale"],
                "contradictions": list(pkt["contradictions"]),
                "falsifiers": list(pkt["falsifiers"]),
            },
            "post_packet": {
                "authorship_kind": post["authorship_kind"],
                "operator_id": post["operator_id"],
                "sealed_at": post["sealed_at"],
                "action": post["action"],
                "portfolio_action": post["portfolio_action"],
                "rationale": post["rationale"],
                "missing_evidence": list(post["missing_evidence"]),
                "falsifiers": list(post["falsifiers"]),
                "contradictions_recognized": list(post["contradictions_recognized"]),
            },
            "rubric": {
                "authorship_kind": rubric["authorship_kind"],
                "reviewer_id": rubric["reviewer_id"],
                "scored_at": rubric["scored_at"],
                "baseline": baseline_totals,
                "post_packet": post_totals,
            },
            "delta": {
                "action_change": baseline["action"] != post["action"],
                "baseline_action": baseline["action"],
                "post_action": post["action"],
                "rubric_item_deltas": item_deltas,
                "total_score_difference": total_delta,
                "total_score_difference_raw_note": (
                    "Signed difference encoded as magnitude+is_negative+"
                    "value_string because canonical integers are non-negative."
                ),
                "missing_evidence_delta": list(post["missing_evidence"]),
                "falsifier_delta": list(post["falsifiers"]),
                "interpretation": "observed_within_case_difference_only",
            },
        }
    )
    comparison["comparison_hash"] = domain_hash(DOMAIN_COMPARISON, comparison)
    return _freeze(comparison)


def build_result_document(comparison: Mapping[str, Any]) -> Mapping[str, Any]:
    plain = _plain(comparison)
    claimed = _require_sha256(plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID")
    body = _without_keys(plain, "comparison_hash")
    recomputed = domain_hash(DOMAIN_COMPARISON, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")
    result_body = {
        "schema_version": "gv_e0b_dv1_result_v1",
        "case_id": CASE_ID,
        "run_class": RUN_CLASS_SYNTHETIC,
        "comparison": plain,
        "claim_boundary": (
            "Observed within-case difference only. No causal superiority, "
            "general decision-quality improvement, research-efficiency, alpha, "
            "or score uplift claim. Engine fixtures do not count as observed "
            "comparisons."
        ),
    }
    result_hash = domain_hash(DOMAIN_RESULT, result_body)
    out = dict(result_body)
    out["result_hash"] = result_hash
    return _freeze(out)


def build_decision_packet_markdown(comparison: Mapping[str, Any]) -> str:
    c = _plain(comparison)
    lines = [
        "# GV-E0B-DV1 Decision Packet — G08 Contradiction Case",
        "",
        f"- case_id: `{c['case_id']}`",
        f"- run_class: `{c['run_class']}`",
        f"- acceptance_case: `{c['acceptance_case']}`",
        f"- comparison_hash: `{c['comparison_hash']}`",
        f"- bundle_hash: `{c['bundle_hash']}`",
        f"- baseline_hash: `{c['baseline_hash']}`",
        f"- packet_hash: `{c['packet_hash']}`",
        f"- post_packet_hash: `{c['post_packet_hash']}`",
        f"- rubric_hash: `{c['rubric_hash']}`",
        f"- observed_comparison_count: `{c['stage_claim']['observed_comparison_count']}`",
        f"- e0b_close_eligible: `{c['stage_claim']['e0b_close_eligible']}`",
        f"- shipped_product_score: `39` (frozen)",
        f"- functional_stage: `{c['stage_claim']['functional_stage']}`",
        "",
        "## Baseline",
        f"- authorship: `{c['baseline']['authorship_kind']}` / `{c['baseline']['operator_id']}`",
        f"- sealed_at: `{c['baseline']['sealed_at']}`",
        f"- action: `{c['baseline']['action']}`",
        f"- rationale: {c['baseline']['rationale']}",
        "",
        "## GodView packet",
        f"- run_state: `{c['godview_packet']['run_state']}`",
        f"- block_reason: `{c['godview_packet']['block_reason']}`",
        f"- rationale: {c['godview_packet']['rationale']}",
        "",
        "## Post-packet",
        f"- authorship: `{c['post_packet']['authorship_kind']}` / `{c['post_packet']['operator_id']}`",
        f"- sealed_at: `{c['post_packet']['sealed_at']}`",
        f"- action: `{c['post_packet']['action']}`",
        f"- rationale: {c['post_packet']['rationale']}",
        "",
        "## Rubric delta (observed within-case only)",
        f"- reviewer: `{c['rubric']['reviewer_id']}` ({c['rubric']['authorship_kind']})",
        f"- baseline_total: `{c['rubric']['baseline']['total']}`",
        f"- post_total: `{c['rubric']['post_packet']['total']}`",
        f"- total_score_difference: `{c['delta']['total_score_difference']['value_string']}`",
        f"- action_change: `{c['delta']['action_change']}`",
        "",
        "Interpretation: observed within-case difference only. "
        "No causal or general-effectiveness claim.",
        "",
    ]
    return "\n".join(lines)


def write_canonical_artifacts(
    comparison: Mapping[str, Any],
    *,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
) -> Mapping[str, Any]:
    """Atomically emit result.json and decision_packet.md bound to comparison_hash."""

    result = build_result_document(comparison)
    result_bytes = canonical_document_bytes(_plain(result))
    packet_md = build_decision_packet_markdown(comparison).encode("utf-8")
    _atomic_write_bytes(result_json_path, result_bytes)
    _atomic_write_bytes(decision_packet_path, packet_md)
    # Post-write exact-byte check on JSON.
    if result_json_path.read_bytes() != result_bytes:
        raise GvE0bDv1Error("E0B_RESULT_JSON_VERIFY_FAILED")
    return result


def e0b_rationale_ref(comparison_hash: str) -> str:
    digest = _require_sha256(comparison_hash, "E0B_COMPARISON_HASH_INVALID")
    ref = f"{RATIONALE_REF_PREFIX}{digest}"
    if len(ref) > 128:
        raise GvE0bDv1Error("E0B_RATIONALE_REF_TOO_LONG")
    return ref


def build_e0b_decision(
    fixture_hash: str,
    fixture_id: str,
    *,
    rationale_ref: str,
) -> DecisionEnvelope:
    if not rationale_ref.startswith(RATIONALE_REF_PREFIX):
        raise GvE0bDv1Error("E0B_RATIONALE_REF_PREFIX_INVALID")
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id=E0B_DECISION_ID,
        action=PORTFOLIO_ACTION_NO_POSITION,
        requested_quantity=None,
        rationale_ref=rationale_ref,
    )


def build_e0b_book(*, comparison_hash: str) -> OpenBookBuild:
    rationale_ref = e0b_rationale_ref(comparison_hash)

    def decision_builder(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
        return build_e0b_decision(
            fixture_hash,
            fixture_id,
            rationale_ref=rationale_ref,
        )

    return _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )


def build_e0b_certified_result(
    comparison: Mapping[str, Any],
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    plain = _plain(comparison)
    comparison_hash = _require_sha256(
        plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID"
    )
    # Recompute comparison seal.
    body = _without_keys(plain, "comparison_hash")
    if domain_hash(DOMAIN_COMPARISON, body) != comparison_hash:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")
    certified = build_certified_result_from_book(
        build_e0b_book(comparison_hash=comparison_hash),
        verifier_runner,
    )
    decision = certified.get("decision") or {}
    expected_ref = e0b_rationale_ref(comparison_hash)
    if decision.get("decision_id") != E0B_DECISION_ID:
        raise GvE0bDv1Error("E0B_CERT_DECISION_ID_MISMATCH")
    if decision.get("rationale_ref") != expected_ref:
        raise GvE0bDv1Error("E0B_CERT_RATIONALE_BINDING_INVALID")
    if decision.get("action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvE0bDv1Error("E0B_CERT_ACTION_MISMATCH")
    if certified.get("certification", {}).get("certification_status") != "CERTIFIED":
        raise GvE0bDv1Error("E0B_CERT_STATUS_REQUIRED")
    return certified


def publish_e0b_current_decision(
    comparison: Mapping[str, Any],
    *,
    target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    lock_path: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> CurrentDecisionPublicationResult:
    """Certify and publish comparison-bound E0B decision (SYNTHETIC_DEV_RUN case)."""

    certified = build_e0b_certified_result(comparison, verifier_runner)
    return publish_current_decision(certified, target=target, lock_path=lock_path)


def run_e0b_dv1_case(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
    publish: bool = False,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> Mapping[str, Any]:
    """One-case path: seals → comparison → artifacts → optional cert/publish."""

    comparison = build_comparison(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
    )
    result = write_canonical_artifacts(
        comparison,
        result_json_path=result_json_path,
        decision_packet_path=decision_packet_path,
    )
    published = None
    if publish:
        published = publish_e0b_current_decision(
            comparison,
            target=current_target,
            lock_path=current_lock,
            verifier_runner=verifier_runner,
        )
    return _freeze(
        {
            "comparison": comparison,
            "result": result,
            "published": None
            if published is None
            else {
                "status": published.status,
                "target_path": published.target_path,
                "certified_decision_result_hash": published.certified_decision_result_hash,
            },
            "observed_comparison_count": comparison["stage_claim"][
                "observed_comparison_count"
            ],
            "e0b_close_eligible": comparison["stage_claim"]["e0b_close_eligible"],
            "run_class": RUN_CLASS_SYNTHETIC,
        }
    )


def build_comparison_presentation(comparison: Mapping[str, Any]) -> Mapping[str, Any]:
    c = _plain(comparison)
    rows = [
        {"label": "Case", "value": str(c["case_id"])},
        {"label": "AcceptanceCase", "value": "G08"},
        {"label": "RunClass", "value": RUN_CLASS_SYNTHETIC},
        {
            "label": "GodViewRunState",
            "value": str(c["godview_packet"]["run_state"]),
        },
        {
            "label": "BlockReason",
            "value": str(c["godview_packet"]["block_reason"]),
        },
        {
            "label": "BaselineAuthorship",
            "value": str(c["baseline"]["authorship_kind"]),
        },
        {
            "label": "BaselineAction",
            "value": str(c["baseline"]["action"]),
        },
        {
            "label": "PostPacketAuthorship",
            "value": str(c["post_packet"]["authorship_kind"]),
        },
        {
            "label": "PostPacketAction",
            "value": str(c["post_packet"]["action"]),
        },
        {
            "label": "ActionChange",
            "value": "TRUE" if c["delta"]["action_change"] else "FALSE",
        },
        {
            "label": "RubricTotalDelta",
            "value": str(c["delta"]["total_score_difference"]["value_string"]),
        },
        {
            "label": "Reviewer",
            "value": f"{c['rubric']['reviewer_id']} ({c['rubric']['authorship_kind']})",
        },
        {
            "label": "ObservedComparisonCount",
            "value": str(c["stage_claim"]["observed_comparison_count"]),
        },
        {
            "label": "E0BCloseEligible",
            "value": "TRUE" if c["stage_claim"]["e0b_close_eligible"] else "FALSE",
        },
        {
            "label": "ComparisonHash",
            "value": str(c["comparison_hash"]),
        },
        {"label": "AlphaClaim", "value": "FALSE"},
        {"label": "ShippedProductScore", "value": "39"},
        {
            "label": "FunctionalStage",
            "value": "CERTIFIED_SINGLE_DECISION_OPERABLE",
        },
    ]
    return _freeze(
        {
            "title": "GV-E0B-DV1 Decision Delta — G08 Contradiction Case",
            "rows": rows,
        }
    )


def render_e0b_dv1_comparison(
    renderer: Any,
    *,
    comparison: Mapping[str, Any] | None = None,
    result_json_path: Path | None = None,
) -> Mapping[str, Any]:
    """Injected-renderer presentation for one visible comparison."""

    if comparison is None:
        path = result_json_path or DEFAULT_RESULT_JSON
        if not path.is_file():
            raise GvE0bDv1Error("E0B_RESULT_MISSING")
        result = _load_json_object(path)
        comparison = result.get("comparison")
        if not isinstance(comparison, Mapping):
            raise GvE0bDv1Error("E0B_RESULT_COMPARISON_MISSING")
    presentation = build_comparison_presentation(comparison)
    renderer.subheader(presentation["title"])
    renderer.table(list(presentation["rows"]))
    obs = comparison["stage_claim"]["observed_comparison_count"]
    close = comparison["stage_claim"]["e0b_close_eligible"]
    renderer.caption(
        "E0B-DV1 · G08 · SYNTHETIC_DEV_RUN · score 39 frozen · "
        f"observed-comparison count = {obs} · close_eligible={close} · "
        "within-case difference only · no causal/alpha claim"
    )
    return presentation


def observed_comparison_count_from_disk(
    result_json_path: Path = DEFAULT_RESULT_JSON,
) -> int:
    """Report 0 unless a real-human close-eligible result is on disk."""

    if not result_json_path.is_file():
        return 0
    try:
        result = _load_json_object(result_json_path)
        comparison = result.get("comparison")
        if not isinstance(comparison, Mapping):
            return 0
        stage = comparison.get("stage_claim") or {}
        if stage.get("e0b_close_eligible") is True:
            return int(stage.get("observed_comparison_count") or 0)
        return 0
    except GvE0bDv1Error:
        return 0


__all__ = [
    "AUTH_FIXTURE",
    "AUTH_REAL_OPERATOR",
    "AUTH_REAL_REVIEWER",
    "BLOCK_REASON",
    "CASE_ID",
    "DEFAULT_BASELINE_PATH",
    "DEFAULT_DECISION_PACKET_MD",
    "DEFAULT_POST_PATH",
    "DEFAULT_RESULT_JSON",
    "DEFAULT_RUBRIC_PATH",
    "E0B_DECISION_ID",
    "RATIONALE_REF_PREFIX",
    "RUBRIC_ITEMS",
    "RUN_CLASS_SYNTHETIC",
    "GvE0bDv1Error",
    "build_comparison",
    "build_comparison_presentation",
    "build_decision_packet_markdown",
    "build_e0b_book",
    "build_e0b_certified_result",
    "build_e0b_decision",
    "build_godview_packet",
    "build_result_document",
    "e0b_rationale_ref",
    "is_observed_comparison_eligible",
    "load_baseline_seal",
    "load_post_packet_seal",
    "load_rubric_scores",
    "observed_comparison_count_from_disk",
    "publish_e0b_current_decision",
    "render_e0b_dv1_comparison",
    "run_e0b_dv1_case",
    "seal_baseline_record",
    "seal_post_packet_record",
    "seal_rubric_record",
    "sealed_adversarial_bundle",
    "verify_bundle_seal",
    "write_canonical_artifacts",
]
