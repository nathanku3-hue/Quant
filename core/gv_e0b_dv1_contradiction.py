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
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
import tempfile
from types import MappingProxyType
from typing import Any, Protocol

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
DEFAULT_PACKET_PATH = DEFAULT_CASE_DIR / "captures" / "packet.json"
DEFAULT_POST_PATH = DEFAULT_CASE_DIR / "captures" / "post_packet_seal.json"
DEFAULT_RUBRIC_PATH = DEFAULT_CASE_DIR / "captures" / "rubric_scores.json"
DEFAULT_SESSION_PATH = DEFAULT_CASE_DIR / "captures" / "session.json"
DEFAULT_ATTESTATION_PATH = DEFAULT_CASE_DIR / "captures" / "close_attestation.json"

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
DOMAIN_SESSION = "GV-E0B:DV1:SESSION:V1"
DOMAIN_CHAIN = "GV-E0B:DV1:CHAIN:V1"
DOMAIN_ATTESTATION = "GV-E0B:DV1:ATTESTATION:V1"

AUTH_FIXTURE = "ENGINE_TEST_FIXTURE"
AUTH_REAL_OPERATOR = "REAL_HUMAN_OPERATOR"
AUTH_REAL_REVIEWER = "REAL_HUMAN_REVIEWER"
AUTH_EXTERNAL_ATTESTOR = "EXTERNAL_INDEPENDENT_ATTESTOR"

BUDGET_MINUTES = 60
ZERO_CHAIN_HASH = "0" * 64
ARM_BASELINE = "BASELINE"
ARM_POST = "POST"
ARM_RUBRIC = "RUBRIC"
STAGE_SESSION_OPEN = "SESSION_OPEN"
STAGE_BASELINE = "BASELINE"
STAGE_PACKET = "PACKET"
STAGE_POST = "POST"
STAGE_RUBRIC = "RUBRIC"
STAGE_COMPARISON = "COMPARISON"

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


def _utc_now_canonical() -> str:
    """Capture actual UTC wall-clock time in canonical microsecond form."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _require_generated_at(value: Any) -> str:
    if not isinstance(value, str) or not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error("E0B_PACKET_GENERATED_AT_INVALID")
    return value


class CaptureClock(Protocol):
    def now(self) -> str: ...


class WallClock:
    """Production capture clock: actual UTC wall time only."""

    def now(self) -> str:
        return _utc_now_canonical()


class AdvanceableClock:
    """Test-only clock. Production stages must use WallClock."""

    def __init__(self, start: str) -> None:
        if not CANONICAL_TIMESTAMP_RE.fullmatch(start):
            raise GvE0bDv1Error("E0B_CLOCK_START_INVALID")
        self._current = datetime.fromisoformat(start.replace("Z", "+00:00"))

    def now(self) -> str:
        return self._current.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def advance_minutes(self, minutes: int) -> str:
        if minutes < 0:
            raise GvE0bDv1Error("E0B_CLOCK_ADVANCE_NEGATIVE")
        self._current = self._current + timedelta(minutes=int(minutes))
        return self.now()


def _parse_ts(value: str) -> datetime:
    if not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error("E0B_TIMESTAMP_INVALID")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _elapsed_whole_minutes(start: str, end: str) -> int:
    s = _parse_ts(start)
    e = _parse_ts(end)
    if e <= s:
        raise GvE0bDv1Error("E0B_ARM_END_BEFORE_START")
    total = int((e - s).total_seconds())
    if total % 60 != 0:
        raise GvE0bDv1Error("E0B_BUDGET_NOT_WHOLE_MINUTES")
    return total // 60


def _reject_caller_timing_fields(record: Mapping[str, Any]) -> None:
    banned = (
        "sealed_at",
        "arm_started_at",
        "arm_ended_at",
        "session_nonce",
        "prev_chain_hash",
        "human_analysis_time_minutes",
        "scored_at",
        "generated_at",
    )
    for key in banned:
        if key in record:
            raise GvE0bDv1Error(f"E0B_CALLER_TIMING_FORBIDDEN:{key}")


def _chain_link(
    *,
    session_nonce: str,
    stage: str,
    record_hash: str,
    prev_chain_hash: str,
) -> dict[str, Any]:
    body = {
        "session_nonce": session_nonce,
        "stage": stage,
        "record_hash": _require_sha256(record_hash, "E0B_CHAIN_RECORD_HASH_INVALID"),
        "prev_chain_hash": _require_sha256(prev_chain_hash, "E0B_CHAIN_PREV_INVALID"),
    }
    out = dict(body)
    out["chain_hash"] = domain_hash(DOMAIN_CHAIN, body)
    return out


def _session_tip(session: Mapping[str, Any]) -> str:
    entries = list(session.get("chain") or [])
    if not entries:
        return ZERO_CHAIN_HASH
    tip = entries[-1].get("chain_hash")
    return _require_sha256(tip, "E0B_SESSION_TIP_INVALID")


def _append_session_chain(
    session: dict[str, Any],
    *,
    stage: str,
    record_hash: str,
) -> dict[str, Any]:
    link = _chain_link(
        session_nonce=session["session_nonce"],
        stage=stage,
        record_hash=record_hash,
        prev_chain_hash=_session_tip(session),
    )
    chain = list(session.get("chain") or [])
    chain.append(link)
    session["chain"] = chain
    session["session_hash"] = domain_hash(
        DOMAIN_SESSION,
        {
            "case_id": session["case_id"],
            "session_nonce": session["session_nonce"],
            "bundle_hash": session["bundle_hash"],
            "created_at": session["created_at"],
            "chain": chain,
        },
    )
    return link


def verify_session_chain(session: Mapping[str, Any]) -> str:
    plain = _plain(session)
    claimed = _require_sha256(plain.get("session_hash"), "E0B_SESSION_HASH_INVALID")
    chain = list(plain.get("chain") or [])
    if not chain:
        raise GvE0bDv1Error("E0B_SESSION_CHAIN_EMPTY")
    expected_prev = ZERO_CHAIN_HASH
    nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    for idx, entry in enumerate(chain):
        if not isinstance(entry, Mapping):
            raise GvE0bDv1Error(f"E0B_SESSION_ENTRY_INVALID:{idx}")
        body = _without_keys(entry, "chain_hash")
        if body.get("session_nonce") != nonce:
            raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
        if body.get("prev_chain_hash") != expected_prev:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_BREAK:{idx}")
        recomputed = domain_hash(DOMAIN_CHAIN, body)
        claimed_link = _require_sha256(entry.get("chain_hash"), "E0B_CHAIN_HASH_INVALID")
        if recomputed != claimed_link:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_SEAL_MISMATCH:{idx}")
        expected_prev = claimed_link
    body = {
        "case_id": plain["case_id"],
        "session_nonce": nonce,
        "bundle_hash": plain["bundle_hash"],
        "created_at": plain["created_at"],
        "chain": [_plain(e) for e in chain],
    }
    if domain_hash(DOMAIN_SESSION, body) != claimed:
        raise GvE0bDv1Error("E0B_SESSION_SEAL_MISMATCH")
    return claimed


def open_capture_session(
    *,
    bundle: Mapping[str, Any] | None = None,
    session_path: Path = DEFAULT_SESSION_PATH,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    """Open append-only capture session with generated nonce (system-stamped)."""

    clk = clock or WallClock()
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    created_at = clk.now()
    session_nonce = secrets.token_hex(32)
    session: dict[str, Any] = {
        "case_id": CASE_ID,
        "session_nonce": session_nonce,
        "bundle_hash": bndl["bundle_hash"],
        "created_at": created_at,
        "open_arms": {},
        "chain": [],
    }
    open_body = {
        "case_id": CASE_ID,
        "session_nonce": session_nonce,
        "bundle_hash": bndl["bundle_hash"],
        "created_at": created_at,
    }
    open_hash = domain_hash(DOMAIN_SESSION, open_body)
    _append_session_chain(session, stage=STAGE_SESSION_OPEN, record_hash=open_hash)
    _persist_sealed_json(session_path, session)
    return _freeze(session)


def load_capture_session(session_path: Path = DEFAULT_SESSION_PATH) -> dict[str, Any]:
    raw = _load_json_object(session_path)
    verify_session_chain(raw)
    return _plain(raw)


def stage_open_arm(
    arm: str,
    *,
    session_path: Path = DEFAULT_SESSION_PATH,
    clock: CaptureClock | None = None,
) -> str:
    """System-stamp arm start. Caller cannot supply the start timestamp."""

    if arm not in {ARM_BASELINE, ARM_POST, ARM_RUBRIC}:
        raise GvE0bDv1Error("E0B_ARM_UNKNOWN")
    clk = clock or WallClock()
    session = load_capture_session(session_path)
    open_arms = dict(session.get("open_arms") or {})
    if arm in open_arms:
        raise GvE0bDv1Error(f"E0B_ARM_ALREADY_OPEN:{arm}")
    started = clk.now()
    open_arms[arm] = started
    session["open_arms"] = open_arms
    # Recompute session hash after open_arms mutation (open_arms not in seal body).
    session["session_hash"] = domain_hash(
        DOMAIN_SESSION,
        {
            "case_id": session["case_id"],
            "session_nonce": session["session_nonce"],
            "bundle_hash": session["bundle_hash"],
            "created_at": session["created_at"],
            "chain": session["chain"],
        },
    )
    _persist_sealed_json(session_path, session)
    return started


def _without_keys(record: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    banned = set(keys)
    return {k: _plain(v) for k, v in record.items() if k not in banned}


def _persist_sealed_json(path: Path, record: Mapping[str, Any]) -> None:
    """Atomic write of a sealed record as canonical JSON bytes."""

    payload = canonical_document_bytes(_plain(record))
    _atomic_write_bytes(path, payload)


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


def build_godview_packet(
    *,
    bundle: Mapping[str, Any] | None = None,
    generated_at: str,
    session_nonce: str,
    prev_chain_hash: str,
) -> Mapping[str, Any]:
    """G08 packet: BLOCKED on contradictory indispensable evidence.

    ``generated_at`` must be supplied by the capture stage clock (never a
    hardcoded calendar day and never inventable by the human authoring payload).
    Packet is chain-bound via session_nonce + prev_chain_hash.
    """

    b_plain = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(b_plain)
    claims = list(b_plain.get("indispensable_claims") or [])
    if not claims:
        raise GvE0bDv1Error("E0B_BUNDLE_CLAIMS_REQUIRED")
    contradictions = _find_indispensable_contradictions(claims)
    if not contradictions:
        raise GvE0bDv1Error("E0B_G08_EXPECTS_CONTRADICTION")

    ts = _require_generated_at(generated_at)
    body = {
        "case_id": CASE_ID,
        "arm": "GODVIEW_PACKET",
        "bundle_hash": b_plain["bundle_hash"],
        "generated_at": ts,
        "session_nonce": _require_str(
            {"session_nonce": session_nonce}, "session_nonce", "E0B_SESSION_NONCE_REQUIRED"
        ),
        "prev_chain_hash": _require_sha256(prev_chain_hash, "E0B_CHAIN_PREV_INVALID"),
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
    """Validate decision content. Timing/budget fields are system-stamped only."""

    plain = _require_mapping(record, "E0B_DECISION_RECORD_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    if plain.get("arm") != expected_arm:
        raise GvE0bDv1Error("E0B_ARM_MISMATCH")
    auth = _require_str(plain, "authorship_kind", "E0B_AUTHORSHIP_REQUIRED")
    if auth not in allowed_auth:
        raise GvE0bDv1Error("E0B_AUTHORSHIP_INVALID")
    operator_id = _require_str(plain, "operator_id", "E0B_OPERATOR_REQUIRED")
    arm_started_at = _require_timestamp(plain, "arm_started_at", "E0B_ARM_STARTED_REQUIRED")
    arm_ended_at = _require_timestamp(plain, "arm_ended_at", "E0B_ARM_ENDED_REQUIRED")
    measured = _elapsed_whole_minutes(arm_started_at, arm_ended_at)
    if measured != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_NOT_60")
    session_nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    prev_chain_hash = _require_sha256(
        plain.get("prev_chain_hash"), "E0B_CHAIN_PREV_INVALID"
    )
    sealed_at = arm_ended_at
    if "sealed_at" in plain and plain["sealed_at"] != sealed_at:
        raise GvE0bDv1Error("E0B_SEALED_AT_MUST_MATCH_ARM_END")
    if "human_analysis_time_minutes" in plain and plain["human_analysis_time_minutes"] != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_FIELD_MISMATCH")
    bundle_hash = _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
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
        "arm_started_at": arm_started_at,
        "arm_ended_at": arm_ended_at,
        "sealed_at": sealed_at,
        "session_nonce": session_nonce,
        "prev_chain_hash": prev_chain_hash,
        "bundle_hash": bundle_hash,
        "human_analysis_time_minutes": BUDGET_MINUTES,
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
    """Load a *pre-sealed* baseline. Unsealed authoring payloads are rejected."""

    raw = _load_json_object(path)
    if "baseline_hash" not in raw:
        raise GvE0bDv1Error("E0B_BASELINE_UNSEALED")
    verify_baseline_seal(raw)
    sealed = _freeze(_plain(raw))
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
    if body["session_nonce"] != b["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if body["session_nonce"] != p.get("session_nonce"):
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
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
    """Load a *pre-sealed* post decision. Unsealed authoring payloads are rejected."""

    raw = _load_json_object(path)
    if "post_packet_hash" not in raw:
        raise GvE0bDv1Error("E0B_POST_UNSEALED")
    verify_post_packet_seal(raw, packet=packet, baseline=baseline)
    return _freeze(_plain(raw))


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
    arm_started_at = _require_timestamp(plain, "arm_started_at", "E0B_ARM_STARTED_REQUIRED")
    arm_ended_at = _require_timestamp(plain, "arm_ended_at", "E0B_ARM_ENDED_REQUIRED")
    measured = _elapsed_whole_minutes(arm_started_at, arm_ended_at)
    if measured != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_NOT_60")
    scored_at = arm_ended_at
    if "scored_at" in plain and plain["scored_at"] != scored_at:
        raise GvE0bDv1Error("E0B_SCORED_AT_MUST_MATCH_ARM_END")
    if scored_at < p["sealed_at"]:
        raise GvE0bDv1Error("E0B_RUBRIC_BEFORE_POST_FORBIDDEN")
    if arm_started_at < p["sealed_at"]:
        raise GvE0bDv1Error("E0B_RUBRIC_ARM_BEFORE_POST_FORBIDDEN")
    session_nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    prev_chain_hash = _require_sha256(
        plain.get("prev_chain_hash"), "E0B_CHAIN_PREV_INVALID"
    )
    if session_nonce != b["session_nonce"] or session_nonce != p["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if session_nonce != pkt.get("session_nonce"):
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
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
        "arm_started_at": arm_started_at,
        "arm_ended_at": arm_ended_at,
        "scored_at": scored_at,
        "session_nonce": session_nonce,
        "prev_chain_hash": prev_chain_hash,
        "human_analysis_time_minutes": BUDGET_MINUTES,
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
    """Load *pre-sealed* rubric scores. Unsealed authoring payloads are rejected."""

    raw = _load_json_object(path)
    if "rubric_hash" not in raw:
        raise GvE0bDv1Error("E0B_RUBRIC_UNSEALED")
    verify_rubric_seal(raw, baseline=baseline, post=post, packet=packet)
    return _freeze(_plain(raw))


def load_packet_seal(path: Path) -> Mapping[str, Any]:
    """Load a *pre-sealed* GodView packet. Unsealed payloads are rejected."""

    raw = _load_json_object(path)
    if "packet_hash" not in raw:
        raise GvE0bDv1Error("E0B_PACKET_UNSEALED")
    verify_packet_seal(raw)
    return _freeze(_plain(raw))


def score_totals(arm_scores: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    items = {item: int(arm_scores[item]["score"]) for item in RUBRIC_ITEMS}
    return {
        "items": items,
        "total": sum(items.values()),
        "max_total": 2 * len(RUBRIC_ITEMS),
    }


def is_attribution_structure_valid(
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> bool:
    """Human ID labels are attribution only — never sufficient for close."""

    return (
        baseline.get("authorship_kind") == AUTH_REAL_OPERATOR
        and post.get("authorship_kind") == AUTH_REAL_OPERATOR
        and baseline.get("operator_id") == post.get("operator_id")
        and rubric.get("authorship_kind") == AUTH_REAL_REVIEWER
        and rubric.get("reviewer_id") != baseline.get("operator_id")
    )


def seal_close_attestation(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """External independent attestation required for e0b_close_eligible."""

    plain = _require_mapping(record, "E0B_ATTESTATION_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    if plain.get("authorship_kind") != AUTH_EXTERNAL_ATTESTOR:
        raise GvE0bDv1Error("E0B_ATTESTOR_KIND_REQUIRED")
    attestor_id = _require_str(plain, "attestor_id", "E0B_ATTESTOR_REQUIRED")
    operator_id = _require_str(plain, "operator_id", "E0B_OPERATOR_REQUIRED")
    reviewer_id = _require_str(plain, "reviewer_id", "E0B_REVIEWER_REQUIRED")
    if attestor_id in {operator_id, reviewer_id}:
        raise GvE0bDv1Error("E0B_ATTESTOR_MUST_BE_INDEPENDENT")
    comparison_hash = _require_sha256(
        plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID"
    )
    session_nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    attested_at = _require_timestamp(plain, "attested_at", "E0B_ATTESTED_AT_INVALID")
    if plain.get("fresh_operator_attested") is not True:
        raise GvE0bDv1Error("E0B_FRESH_OPERATOR_REQUIRED")
    if plain.get("blinded_reviewer_attested") is not True:
        raise GvE0bDv1Error("E0B_BLINDED_REVIEWER_REQUIRED")
    if plain.get("operator_had_not_seen_packet_or_expected_outcome") is not True:
        raise GvE0bDv1Error("E0B_OPERATOR_MUST_BE_UNSEEN")
    notes = plain.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise GvE0bDv1Error("E0B_ATTESTATION_NOTES_REQUIRED")
    body = {
        "case_id": CASE_ID,
        "authorship_kind": AUTH_EXTERNAL_ATTESTOR,
        "attestor_id": attestor_id,
        "operator_id": operator_id,
        "reviewer_id": reviewer_id,
        "comparison_hash": comparison_hash,
        "session_nonce": session_nonce,
        "attested_at": attested_at,
        "fresh_operator_attested": True,
        "blinded_reviewer_attested": True,
        "operator_had_not_seen_packet_or_expected_outcome": True,
        "notes": notes.strip(),
    }
    out = dict(body)
    out["attestation_hash"] = domain_hash(DOMAIN_ATTESTATION, body)
    return _freeze(out)


def verify_close_attestation(
    attestation: Mapping[str, Any],
    *,
    comparison_hash: str,
    operator_id: str,
    reviewer_id: str,
    session_nonce: str,
) -> str:
    plain = _plain(attestation)
    claimed = _require_sha256(plain.get("attestation_hash"), "E0B_ATTESTATION_HASH_INVALID")
    body = _without_keys(plain, "attestation_hash")
    sealed = seal_close_attestation(body)
    if sealed["attestation_hash"] != claimed:
        raise GvE0bDv1Error("E0B_ATTESTATION_SEAL_MISMATCH")
    if sealed["comparison_hash"] != comparison_hash:
        raise GvE0bDv1Error("E0B_ATTESTATION_COMPARISON_MISMATCH")
    if sealed["operator_id"] != operator_id or sealed["reviewer_id"] != reviewer_id:
        raise GvE0bDv1Error("E0B_ATTESTATION_IDENTITY_MISMATCH")
    if sealed["session_nonce"] != session_nonce:
        raise GvE0bDv1Error("E0B_ATTESTATION_SESSION_MISMATCH")
    return claimed


def is_observed_comparison_eligible(
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    rubric: Mapping[str, Any],
    *,
    attestation: Mapping[str, Any] | None = None,
    comparison_hash: str | None = None,
) -> bool:
    """True only with external independent attestation.

    REAL_HUMAN_* labels are attribution only and never close E0B alone.
    """

    if attestation is None or comparison_hash is None:
        return False
    if not is_attribution_structure_valid(baseline, post, rubric):
        return False
    try:
        verify_close_attestation(
            attestation,
            comparison_hash=comparison_hash,
            operator_id=str(baseline.get("operator_id")),
            reviewer_id=str(rubric.get("reviewer_id")),
            session_nonce=str(baseline.get("session_nonce")),
        )
    except GvE0bDv1Error:
        return False
    return True


def build_comparison(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    bundle: Mapping[str, Any] | None = None,
    packet: Mapping[str, Any] | None = None,
    packet_path: Path | None = None,
    session_path: Path | None = None,
    attestation: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Assemble comparison from *pre-sealed* external records; never invent outcomes.

    Comparison seal always records observed_comparison_count=0 and
    e0b_close_eligible=False. Close authority is result-level: embedded complete
    seals + external independent attestation bound to comparison_hash.
    REAL_HUMAN_* labels alone never close.
    """

    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    if packet is not None:
        pkt = _plain(packet)
        verify_packet_seal(pkt)
    elif packet_path is not None:
        pkt = _plain(load_packet_seal(packet_path))
    else:
        raise GvE0bDv1Error("E0B_PACKET_REQUIRED")
    if pkt["bundle_hash"] != bndl["bundle_hash"]:
        raise GvE0bDv1Error("E0B_PACKET_BUNDLE_MISMATCH")

    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    if not (baseline["sealed_at"] < pkt["generated_at"]):
        raise GvE0bDv1Error("E0B_INVALID_BASELINE_SEAL")
    if baseline.get("session_nonce") != pkt.get("session_nonce"):
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    post = load_post_packet_seal(post_path, packet=pkt, baseline=baseline)
    rubric = load_rubric_scores(
        rubric_path, baseline=baseline, post=post, packet=pkt
    )
    session = None
    if session_path is not None:
        session = load_capture_session(session_path)
        if session["session_nonce"] != baseline["session_nonce"]:
            raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")

    baseline_totals = score_totals(rubric["baseline_scores"])
    post_totals = score_totals(rubric["post_scores"])
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
    # Labels alone never grant close; comparison seal freezes count at 0.
    attribution_ok = is_attribution_structure_valid(baseline, post, rubric)

    comparison = _plain(
        {
            "case_id": CASE_ID,
            "acceptance_case": "G08",
            "run_class": RUN_CLASS_SYNTHETIC,
            "session_nonce": baseline["session_nonce"],
            "stage_claim": {
                "shipped_product_score": 39,
                "score_frozen": True,
                "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
                "target_stage": "ONE_CASE_DECISION_DELTA_OBSERVED",
                "observed_comparison_count": 0,
                "e0b_close_eligible": False,
                "attribution_structure_valid": attribution_ok,
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
                "session_nonce": baseline["session_nonce"],
                "arm_started_at": baseline["arm_started_at"],
                "arm_ended_at": baseline["arm_ended_at"],
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
                "session_nonce": pkt["session_nonce"],
                "rationale": pkt["rationale"],
                "contradictions": list(pkt["contradictions"]),
                "falsifiers": list(pkt["falsifiers"]),
            },
            "post_packet": {
                "authorship_kind": post["authorship_kind"],
                "operator_id": post["operator_id"],
                "session_nonce": post["session_nonce"],
                "arm_started_at": post["arm_started_at"],
                "arm_ended_at": post["arm_ended_at"],
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
                "session_nonce": rubric["session_nonce"],
                "arm_started_at": rubric["arm_started_at"],
                "arm_ended_at": rubric["arm_ended_at"],
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
    # Attestation may be checked later at result layer against this hash.
    if attestation is not None:
        # Presence alone does not flip comparison stage_claim (hash stable).
        verify_close_attestation(
            attestation,
            comparison_hash=comparison["comparison_hash"],
            operator_id=str(baseline["operator_id"]),
            reviewer_id=str(rubric["reviewer_id"]),
            session_nonce=str(baseline["session_nonce"]),
        )
    return _freeze(comparison)


def build_result_document(
    comparison: Mapping[str, Any],
    *,
    sealed_records: Mapping[str, Any],
    attestation: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Build result embedding complete sealed records for full replay verify."""

    plain = _plain(comparison)
    claimed = _require_sha256(plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID")
    body = _without_keys(plain, "comparison_hash")
    recomputed = domain_hash(DOMAIN_COMPARISON, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")

    seals = _require_mapping(sealed_records, "E0B_SEALED_RECORDS_REQUIRED")
    for key in ("bundle", "baseline", "packet", "post", "rubric", "session"):
        if key not in seals:
            raise GvE0bDv1Error(f"E0B_SEALED_RECORD_MISSING:{key}")

    # Replay every complete seal before hashing the result.
    verify_bundle_seal(seals["bundle"])
    verify_baseline_seal(seals["baseline"])
    verify_packet_seal(seals["packet"])
    verify_post_packet_seal(
        seals["post"], packet=seals["packet"], baseline=seals["baseline"]
    )
    verify_rubric_seal(
        seals["rubric"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
    )
    verify_session_chain(seals["session"])

    if seals["baseline"]["baseline_hash"] != plain["baseline_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_BASELINE_HASH_MISMATCH")
    if seals["packet"]["packet_hash"] != plain["packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_PACKET_HASH_MISMATCH")
    if seals["post"]["post_packet_hash"] != plain["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_POST_HASH_MISMATCH")
    if seals["rubric"]["rubric_hash"] != plain["rubric_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_RUBRIC_HASH_MISMATCH")

    att_plain = _plain(attestation) if attestation is not None else None
    eligible = is_observed_comparison_eligible(
        seals["baseline"],
        seals["post"],
        seals["rubric"],
        attestation=att_plain,
        comparison_hash=claimed,
    )
    close_claim = {
        "e0b_close_eligible": eligible,
        "observed_comparison_count": 1 if eligible else 0,
        "human_ids_are_attribution_only": True,
        "external_attestation_required": True,
    }
    result_body = {
        "schema_version": "gv_e0b_dv1_result_v2",
        "case_id": CASE_ID,
        "run_class": RUN_CLASS_SYNTHETIC,
        "comparison": plain,
        "sealed_records": {
            "bundle": _plain(seals["bundle"]),
            "baseline": _plain(seals["baseline"]),
            "packet": _plain(seals["packet"]),
            "post": _plain(seals["post"]),
            "rubric": _plain(seals["rubric"]),
            "session": _plain(seals["session"]),
        },
        "external_close_attestation": att_plain,
        "close_claim": close_claim,
        "claim_boundary": (
            "Observed within-case difference only. No causal superiority, "
            "general decision-quality improvement, research-efficiency, alpha, "
            "or score uplift claim. REAL_HUMAN labels are attribution only. "
            "Close requires external independent attestation and full seal replay. "
            "Engine fixtures do not count as observed comparisons."
        ),
    }
    result_hash = domain_hash(DOMAIN_RESULT, result_body)
    out = dict(result_body)
    out["result_hash"] = result_hash
    return _freeze(out)


def verify_comparison_document(comparison: Mapping[str, Any]) -> Mapping[str, Any]:
    """Recompute comparison seal; comparison stage close fields stay frozen false/0."""

    plain = _plain(comparison)
    claimed = _require_sha256(
        plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID"
    )
    body = _without_keys(plain, "comparison_hash")
    if domain_hash(DOMAIN_COMPARISON, body) != claimed:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")
    stage = body.get("stage_claim")
    if not isinstance(stage, Mapping):
        raise GvE0bDv1Error("E0B_STAGE_CLAIM_REQUIRED")
    if stage.get("observed_comparison_count") != 0:
        raise GvE0bDv1Error("E0B_COMPARISON_COUNT_MUST_BE_ZERO")
    if stage.get("e0b_close_eligible") is not False:
        raise GvE0bDv1Error("E0B_COMPARISON_CLOSE_MUST_BE_FALSE")
    if stage.get("shipped_product_score") != 39 or stage.get("score_frozen") is not True:
        raise GvE0bDv1Error("E0B_SCORE_FREEZE_VIOLATION")
    if stage.get("functional_stage") != "CERTIFIED_SINGLE_DECISION_OPERABLE":
        raise GvE0bDv1Error("E0B_STAGE_FREEZE_VIOLATION")
    if stage.get("alpha_claim") is not False:
        raise GvE0bDv1Error("E0B_ALPHA_CLAIM_FORBIDDEN")
    return _freeze(plain)


def verify_result_document(result: Mapping[str, Any]) -> Mapping[str, Any]:
    """Full replay: result hash, comparison hash, every complete seal, attestation."""

    plain = _plain(result)
    claimed = _require_sha256(plain.get("result_hash"), "E0B_RESULT_HASH_INVALID")
    body = _without_keys(plain, "result_hash")
    if domain_hash(DOMAIN_RESULT, body) != claimed:
        raise GvE0bDv1Error("E0B_RESULT_SEAL_MISMATCH")
    comparison = body.get("comparison")
    if not isinstance(comparison, Mapping):
        raise GvE0bDv1Error("E0B_RESULT_COMPARISON_MISSING")
    verify_comparison_document(comparison)
    seals = body.get("sealed_records")
    if not isinstance(seals, Mapping):
        raise GvE0bDv1Error("E0B_SEALED_RECORDS_REQUIRED")
    # Replay seals (not merely rehash the summary).
    verify_bundle_seal(seals["bundle"])
    verify_baseline_seal(seals["baseline"])
    verify_packet_seal(seals["packet"])
    verify_post_packet_seal(
        seals["post"], packet=seals["packet"], baseline=seals["baseline"]
    )
    verify_rubric_seal(
        seals["rubric"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
    )
    verify_session_chain(seals["session"])
    if seals["baseline"]["baseline_hash"] != comparison["baseline_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_BASELINE_HASH_MISMATCH")
    if seals["packet"]["packet_hash"] != comparison["packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_PACKET_HASH_MISMATCH")
    if seals["post"]["post_packet_hash"] != comparison["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_POST_HASH_MISMATCH")
    if seals["rubric"]["rubric_hash"] != comparison["rubric_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_RUBRIC_HASH_MISMATCH")

    att = body.get("external_close_attestation")
    eligible = is_observed_comparison_eligible(
        seals["baseline"],
        seals["post"],
        seals["rubric"],
        attestation=att if isinstance(att, Mapping) else None,
        comparison_hash=comparison["comparison_hash"],
    )
    close_claim = body.get("close_claim") or {}
    if close_claim.get("e0b_close_eligible") is not eligible:
        raise GvE0bDv1Error("E0B_CLOSE_CLAIM_MISMATCH")
    expected_count = 1 if eligible else 0
    if int(close_claim.get("observed_comparison_count", -1)) != expected_count:
        raise GvE0bDv1Error("E0B_OBSERVED_COUNT_MISMATCH")
    return _freeze(plain)


def load_verified_result(path: Path) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    return verify_result_document(raw)


def stage_capture_baseline(
    authoring: Mapping[str, Any],
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    """Stage 1 close: system-stamp arm end, enforce 60m budget, seal + chain."""

    clk = clock or WallClock()
    _reject_caller_timing_fields(authoring)
    session = load_capture_session(session_path)
    open_arms = dict(session.get("open_arms") or {})
    started = open_arms.pop(ARM_BASELINE, None)
    if not isinstance(started, str):
        raise GvE0bDv1Error("E0B_BASELINE_ARM_NOT_OPEN")
    ended = clk.now()
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    if session["bundle_hash"] != bndl["bundle_hash"]:
        raise GvE0bDv1Error("E0B_SESSION_BUNDLE_MISMATCH")
    record = {
        **_plain(authoring),
        "arm_started_at": started,
        "arm_ended_at": ended,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip(session),
        "bundle_hash": bndl["bundle_hash"],
        "equal_budget_attestation": True,
    }
    sealed = seal_baseline_record(record)
    _append_session_chain(
        session, stage=STAGE_BASELINE, record_hash=sealed["baseline_hash"]
    )
    session["open_arms"] = open_arms
    _persist_sealed_json(baseline_path, sealed)
    _persist_sealed_json(session_path, session)
    return sealed


def stage_generate_packet(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    """Stage 2: system-stamp packet time after sealed baseline; chain-append."""

    clk = clock or WallClock()
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    baseline = load_baseline_seal(
        baseline_path, expected_bundle_hash=bndl["bundle_hash"]
    )
    if baseline["session_nonce"] != session["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    ts = clk.now()
    if not (baseline["sealed_at"] < ts):
        raise GvE0bDv1Error("E0B_PACKET_MUST_FOLLOW_BASELINE")
    packet = build_godview_packet(
        bundle=bndl,
        generated_at=ts,
        session_nonce=session["session_nonce"],
        prev_chain_hash=_session_tip(session),
    )
    _append_session_chain(
        session, stage=STAGE_PACKET, record_hash=packet["packet_hash"]
    )
    _persist_sealed_json(packet_path, packet)
    _persist_sealed_json(session_path, session)
    return packet


def stage_capture_post(
    authoring: Mapping[str, Any],
    *,
    post_path: Path = DEFAULT_POST_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    """Stage 3: system-stamp post arm end, 60m budget, seal + chain."""

    clk = clock or WallClock()
    _reject_caller_timing_fields(authoring)
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    open_arms = dict(session.get("open_arms") or {})
    started = open_arms.pop(ARM_POST, None)
    if not isinstance(started, str):
        raise GvE0bDv1Error("E0B_POST_ARM_NOT_OPEN")
    ended = clk.now()
    baseline = load_baseline_seal(
        baseline_path, expected_bundle_hash=bndl["bundle_hash"]
    )
    packet = load_packet_seal(packet_path)
    record = {
        **_plain(authoring),
        "arm_started_at": started,
        "arm_ended_at": ended,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip(session),
        "bundle_hash": bndl["bundle_hash"],
        "equal_budget_attestation": True,
    }
    sealed = seal_post_packet_record(record, packet=packet, baseline=baseline)
    _append_session_chain(
        session, stage=STAGE_POST, record_hash=sealed["post_packet_hash"]
    )
    session["open_arms"] = open_arms
    _persist_sealed_json(post_path, sealed)
    _persist_sealed_json(session_path, session)
    return sealed


def stage_capture_rubric(
    authoring: Mapping[str, Any],
    *,
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    post_path: Path = DEFAULT_POST_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    """Stage 4: system-stamp rubric arm end, 60m budget, seal + chain."""

    clk = clock or WallClock()
    _reject_caller_timing_fields(authoring)
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    open_arms = dict(session.get("open_arms") or {})
    started = open_arms.pop(ARM_RUBRIC, None)
    if not isinstance(started, str):
        raise GvE0bDv1Error("E0B_RUBRIC_ARM_NOT_OPEN")
    ended = clk.now()
    baseline = load_baseline_seal(
        baseline_path, expected_bundle_hash=bndl["bundle_hash"]
    )
    packet = load_packet_seal(packet_path)
    post = load_post_packet_seal(post_path, packet=packet, baseline=baseline)
    record = {
        **_plain(authoring),
        "arm_started_at": started,
        "arm_ended_at": ended,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip(session),
        "equal_budget_attestation": True,
    }
    sealed = seal_rubric_record(
        record, baseline=baseline, post=post, packet=packet
    )
    _append_session_chain(
        session, stage=STAGE_RUBRIC, record_hash=sealed["rubric_hash"]
    )
    session["open_arms"] = open_arms
    _persist_sealed_json(rubric_path, sealed)
    _persist_sealed_json(session_path, session)
    return sealed


def _collect_sealed_records(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    packet_path: Path,
    session_path: Path,
    bundle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    packet = load_packet_seal(packet_path)
    post = load_post_packet_seal(post_path, packet=packet, baseline=baseline)
    rubric = load_rubric_scores(
        rubric_path, baseline=baseline, post=post, packet=packet
    )
    session = load_capture_session(session_path)
    return {
        "bundle": bndl,
        "baseline": _plain(baseline),
        "packet": _plain(packet),
        "post": _plain(post),
        "rubric": _plain(rubric),
        "session": session,
    }


def stage_compare(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    post_path: Path = DEFAULT_POST_PATH,
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
    attestation_path: Path | None = None,
    bundle: Mapping[str, Any] | None = None,
    publish: bool = False,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> Mapping[str, Any]:
    """Stage 5: comparison over pre-sealed captures + embedded-seal result."""

    return run_e0b_dv1_case(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path,
        session_path=session_path,
        attestation_path=attestation_path,
        result_json_path=result_json_path,
        decision_packet_path=decision_packet_path,
        bundle=bundle,
        publish=publish,
        current_target=current_target,
        current_lock=current_lock,
        verifier_runner=verifier_runner,
    )


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
    sealed_records: Mapping[str, Any],
    attestation: Mapping[str, Any] | None = None,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
) -> Mapping[str, Any]:
    """Atomically emit result.json and decision_packet.md bound to comparison_hash."""

    result = build_result_document(
        comparison, sealed_records=sealed_records, attestation=attestation
    )
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
    close_eligible: bool = False,
) -> CurrentDecisionPublicationResult:
    """Publish comparison-bound current decision only when close-eligible.

    Fixture certification may still call ``build_e0b_certified_result`` in tests.
    Current portfolio authority publication requires verified close eligibility
    (external attestation + full seal replay), not REAL_HUMAN labels alone.
    """

    verified = verify_comparison_document(comparison)
    if close_eligible is not True:
        raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_CLOSE_ELIGIBLE")
    certified = build_e0b_certified_result(verified, verifier_runner)
    # Bind cert decision to comparison hash before publication.
    decision = certified.get("decision") or {}
    expected_ref = e0b_rationale_ref(verified["comparison_hash"])
    if decision.get("rationale_ref") != expected_ref:
        raise GvE0bDv1Error("E0B_CERT_RATIONALE_BINDING_INVALID")
    return publish_current_decision(certified, target=target, lock_path=lock_path)


def run_e0b_dv1_case(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    packet_path: Path | None = None,
    session_path: Path | None = None,
    attestation_path: Path | None = None,
    packet: Mapping[str, Any] | None = None,
    bundle: Mapping[str, Any] | None = None,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
    publish: bool = False,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> Mapping[str, Any]:
    """One-case path over pre-sealed captures → embedded-seal result → optional publish."""

    if packet_path is None and packet is None:
        raise GvE0bDv1Error("E0B_PACKET_REQUIRED")
    if session_path is None:
        raise GvE0bDv1Error("E0B_SESSION_REQUIRED")
    attestation = None
    if attestation_path is not None and attestation_path.is_file():
        attestation = _load_json_object(attestation_path)
    comparison = build_comparison(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path,
        packet=packet,
        bundle=bundle,
        session_path=session_path,
        attestation=attestation,
    )
    sealed_records = _collect_sealed_records(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path or DEFAULT_PACKET_PATH,
        session_path=session_path,
        bundle=bundle,
    )
    result = write_canonical_artifacts(
        comparison,
        sealed_records=sealed_records,
        attestation=attestation,
        result_json_path=result_json_path,
        decision_packet_path=decision_packet_path,
    )
    verified_result = load_verified_result(result_json_path)
    close = verified_result["close_claim"]
    published = None
    if publish:
        if close["e0b_close_eligible"] is not True:
            raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_CLOSE_ELIGIBLE")
        published = publish_e0b_current_decision(
            comparison,
            target=current_target,
            lock_path=current_lock,
            verifier_runner=verifier_runner,
            close_eligible=True,
        )
    return _freeze(
        {
            "comparison": comparison,
            "result": verified_result,
            "published": None
            if published is None
            else {
                "status": published.status,
                "target_path": published.target_path,
                "certified_decision_result_hash": published.certified_decision_result_hash,
            },
            "observed_comparison_count": close["observed_comparison_count"],
            "e0b_close_eligible": close["e0b_close_eligible"],
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
    """Injected-renderer presentation for one visible comparison.

    Always recomputes comparison/result seals before display. Never trusts
    raw observed-count fields from disk. Close authority is result-level.
    """

    obs = 0
    close = False
    if comparison is None:
        path = result_json_path or DEFAULT_RESULT_JSON
        if not path.is_file():
            raise GvE0bDv1Error("E0B_RESULT_MISSING")
        result = load_verified_result(path)
        comparison = result["comparison"]
        close_claim = result["close_claim"]
        obs = int(close_claim["observed_comparison_count"])
        close = bool(close_claim["e0b_close_eligible"])
    else:
        comparison = verify_comparison_document(comparison)
    presentation = build_comparison_presentation(comparison)
    renderer.subheader(presentation["title"])
    renderer.table(list(presentation["rows"]))
    renderer.caption(
        "E0B-DV1 · G08 · SYNTHETIC_DEV_RUN · score 39 frozen · "
        f"observed-comparison count = {obs} · close_eligible={close} · "
        "within-case difference only · no causal/alpha claim"
    )
    return presentation


def observed_comparison_count_from_disk(
    result_json_path: Path = DEFAULT_RESULT_JSON,
) -> int:
    """Report 0 unless a *verified* close-eligible result is on disk.

    Full seal replay + external attestation required. Labels alone never count.
    """

    if not result_json_path.is_file():
        return 0
    try:
        result = load_verified_result(result_json_path)
        close = result["close_claim"]
        if close.get("e0b_close_eligible") is True:
            return int(close["observed_comparison_count"])
        return 0
    except GvE0bDv1Error:
        return 0


__all__ = [
    "AUTH_EXTERNAL_ATTESTOR",
    "AUTH_FIXTURE",
    "AUTH_REAL_OPERATOR",
    "AUTH_REAL_REVIEWER",
    "AdvanceableClock",
    "BUDGET_MINUTES",
    "BLOCK_REASON",
    "CASE_ID",
    "DEFAULT_ATTESTATION_PATH",
    "DEFAULT_BASELINE_PATH",
    "DEFAULT_DECISION_PACKET_MD",
    "DEFAULT_PACKET_PATH",
    "DEFAULT_POST_PATH",
    "DEFAULT_RESULT_JSON",
    "DEFAULT_RUBRIC_PATH",
    "DEFAULT_SESSION_PATH",
    "E0B_DECISION_ID",
    "RATIONALE_REF_PREFIX",
    "RUBRIC_ITEMS",
    "RUN_CLASS_SYNTHETIC",
    "WallClock",
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
    "is_attribution_structure_valid",
    "is_observed_comparison_eligible",
    "load_baseline_seal",
    "load_capture_session",
    "load_packet_seal",
    "load_post_packet_seal",
    "load_rubric_scores",
    "load_verified_result",
    "observed_comparison_count_from_disk",
    "open_capture_session",
    "publish_e0b_current_decision",
    "render_e0b_dv1_comparison",
    "run_e0b_dv1_case",
    "seal_baseline_record",
    "seal_close_attestation",
    "seal_post_packet_record",
    "seal_rubric_record",
    "sealed_adversarial_bundle",
    "stage_capture_baseline",
    "stage_capture_post",
    "stage_capture_rubric",
    "stage_compare",
    "stage_generate_packet",
    "stage_open_arm",
    "verify_bundle_seal",
    "verify_close_attestation",
    "verify_comparison_document",
    "verify_result_document",
    "verify_session_chain",
    "write_canonical_artifacts",
]
