"""GV-E0B-DV1 Contradiction Case (G08): sealed baseline vs GodView triage delta.

First product decision-value slice after banked E0A substrate. Fully synthetic
adversarial fixture — no provider, no full valuation lattice, no portfolio policy
change. Valid terminal research state is BLOCKED:CONTRADICTORY_INDISPENSABLE_EVIDENCE.

Endpoint authority: docs/architecture/godview_e0/e0_acceptance_tests.md G08.
The engine may not average or majority-vote contradictory indispensable evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.gv_fs0_canonical import domain_hash
from core.gv_fs0_current_decision import (
    DEFAULT_CURRENT_DECISION_PATH,
    parse_current_decision_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPARISON_TARGET = ROOT / "data" / "gv_e0b" / "gv_e0b_dv1_comparison.json"

CASE_ID = "E0B_DV1_G08_CONTRADICTION_1"
PROTOCOL_ID = "GODVIEW-E0-P0-V1"
MODULE = "G_supply"
SUBJECT = "SYNTH_MU_SUPPLY"
BLOCK_REASON = "CONTRADICTORY_INDISPENSABLE_EVIDENCE"
RUN_STATE_BLOCKED = "BLOCKED"
RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"
DOMAIN_BUNDLE = "GV-E0B:DV1:BUNDLE:V1"
DOMAIN_BASELINE = "GV-E0B:DV1:BASELINE:V1"
DOMAIN_PACKET = "GV-E0B:DV1:PACKET:V1"
DOMAIN_POST = "GV-E0B:DV1:POST_PACKET:V1"
DOMAIN_COMPARISON = "GV-E0B:DV1:COMPARISON:V1"

# Frozen six-item rubric from e0_preregistration.yaml baseline.rubric.items
RUBRIC_ITEMS: tuple[str, ...] = (
    "selected_action_defensibility",
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
    "supply_demand_business_shareholder_valuation_claim_separation",
    "avoidance_of_claims_beyond_evidence",
    "rationale_traceability",
)

# Expected E0A NO_POSITION certification binding (banked substrate).
EXPECTED_CERTIFIED_RESULT_HASH = (
    "627c136926ecf947f2ea00f24de85291d44ef5594016f022fac7f2217093d6e6"
)
EXPECTED_DECISION_ID = "DECISION_E0A_HOLD_FOR_EVIDENCE_1"


class GvE0bDv1Error(RuntimeError):
    """Fail-closed E0B-DV1 contradiction-case error."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    """Deep-convert to JSON-canonical plain types (dict/list/scalars)."""

    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def sealed_adversarial_bundle() -> Mapping[str, Any]:
    """Synthetic G08 fixture: two indispensable sources contradict on one fact."""

    bundle = {
        "case_id": CASE_ID,
        "protocol_id": PROTOCOL_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "decision_timestamp": "2026-07-19T12:00:00.000000Z",
        "information_cutoff": "2026-07-19T12:00:00.000000Z",
        "run_class": "SYNTHETIC_DEV_RUN",
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
        ],
    }
    digest = domain_hash(DOMAIN_BUNDLE, bundle)
    out = dict(bundle)
    out["bundle_hash"] = digest
    return _freeze(out)


def sealed_human_baseline(*, bundle: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    """Cheap human baseline sealed before GodView packet (60-minute budget arm)."""

    b = dict(bundle) if bundle is not None else dict(sealed_adversarial_bundle())
    baseline = {
        "case_id": CASE_ID,
        "arm": "HUMAN_BASELINE",
        "sealed_before_packet": True,
        "human_analysis_time_minutes": 60,
        "bundle_hash": b["bundle_hash"],
        "action": "ADVANCE_TO_FULL_RESEARCH",
        "rationale": (
            "Both sources discuss supply relief; advance for deeper research "
            "without resolving the numeric conflict."
        ),
        "missing_evidence": [],
        "falsifiers": [],
        "contradictions_recognized": [],
        "alpha_claim": False,
    }
    baseline["baseline_hash"] = domain_hash(DOMAIN_BASELINE, baseline)
    return _freeze(baseline)


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

    b = dict(bundle) if bundle is not None else dict(sealed_adversarial_bundle())
    claims = list(b.get("indispensable_claims") or [])
    if not claims:
        raise GvE0bDv1Error("E0B_BUNDLE_CLAIMS_REQUIRED")
    contradictions = _find_indispensable_contradictions(claims)
    if not contradictions:
        raise GvE0bDv1Error("E0B_G08_EXPECTS_CONTRADICTION")

    # Explicit anti-average guard: never emit a reconciled numeric mean.
    for item in contradictions:
        values = item["values"]
        if all(isinstance(v, (int, float)) for v in values):
            mean = sum(float(v) for v in values) / len(values)
            item = dict(item)
            item["forbidden_reconciled_mean"] = mean
            # Do not promote mean into any claim value field.

    packet = {
        "case_id": CASE_ID,
        "arm": "GODVIEW_PACKET",
        "bundle_hash": b["bundle_hash"],
        "run_state": RUN_STATE_BLOCKED,
        "block_reason": BLOCK_REASON,
        "acceptance_case": "G08",
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
    packet["packet_hash"] = domain_hash(DOMAIN_PACKET, packet)
    return _freeze(packet)


def sealed_post_packet_decision(
    *,
    bundle: Mapping[str, Any] | None = None,
    packet: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Human decision after GodView packet; must not invent investment conclusion."""

    b = dict(bundle) if bundle is not None else dict(sealed_adversarial_bundle())
    p = dict(packet) if packet is not None else dict(build_godview_packet(bundle=b))
    if p.get("block_reason") != BLOCK_REASON:
        raise GvE0bDv1Error("E0B_POST_REQUIRES_G08_BLOCK")
    post = {
        "case_id": CASE_ID,
        "arm": "HUMAN_POST_PACKET",
        "bundle_hash": b["bundle_hash"],
        "packet_hash": p["packet_hash"],
        "action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "rationale": (
            "After packet: indispensable contradiction on supply-relief timing "
            "blocks advancement; hold for reconciled evidence."
        ),
        "missing_evidence": [
            "reconciled_point_in_time_qualified_sellable_supply_relief_path"
        ],
        "falsifiers": [item["falsifier_id"] for item in p.get("falsifiers", [])],
        "contradictions_recognized": [
            item["fact_key"] for item in p.get("contradictions", [])
        ],
        "alpha_claim": False,
    }
    post["post_packet_hash"] = domain_hash(DOMAIN_POST, post)
    return _freeze(post)


def _rubric_scores_baseline() -> dict[str, int]:
    # Cheap baseline advanced through a contradiction: weak on contradiction items.
    return {
        "selected_action_defensibility": 0,
        "indispensable_missing_evidence_identification": 0,
        "falsifier_and_contradiction_recognition": 0,
        "supply_demand_business_shareholder_valuation_claim_separation": 1,
        "avoidance_of_claims_beyond_evidence": 0,
        "rationale_traceability": 1,
    }


def _rubric_scores_godview_post() -> dict[str, int]:
    # Post-packet hold after explicit G08 block: stronger triage, still no alpha.
    return {
        "selected_action_defensibility": 2,
        "indispensable_missing_evidence_identification": 2,
        "falsifier_and_contradiction_recognition": 2,
        "supply_demand_business_shareholder_valuation_claim_separation": 2,
        "avoidance_of_claims_beyond_evidence": 2,
        "rationale_traceability": 2,
    }


def score_rubric(scores: Mapping[str, int]) -> dict[str, Any]:
    if set(scores) != set(RUBRIC_ITEMS):
        raise GvE0bDv1Error("E0B_RUBRIC_ITEMS_INVALID")
    for item, value in scores.items():
        if value not in (0, 1, 2):
            raise GvE0bDv1Error(f"E0B_RUBRIC_SCORE_INVALID:{item}")
    total = sum(int(scores[item]) for item in RUBRIC_ITEMS)
    return {
        "items": {item: int(scores[item]) for item in RUBRIC_ITEMS},
        "total": total,
        "max_total": 2 * len(RUBRIC_ITEMS),
    }


def load_no_position_cert_binding(
    *,
    current_decision_path: Path | None = None,
) -> Mapping[str, Any]:
    path = current_decision_path or DEFAULT_CURRENT_DECISION_PATH
    if not path.is_file():
        raise GvE0bDv1Error("E0B_CURRENT_DECISION_MISSING")
    try:
        component = parse_current_decision_bytes(path.read_bytes())
    except Exception as exc:  # noqa: BLE001 — bind path fails closed as E0B error
        raise GvE0bDv1Error("E0B_CURRENT_DECISION_INVALID") from exc
    result_hash = component.get("certified_decision_result_hash")
    decision = component.get("decision") or {}
    if result_hash != EXPECTED_CERTIFIED_RESULT_HASH:
        raise GvE0bDv1Error("E0B_CERT_BINDING_HASH_MISMATCH")
    if decision.get("decision_id") != EXPECTED_DECISION_ID:
        raise GvE0bDv1Error("E0B_CERT_BINDING_DECISION_ID_MISMATCH")
    if decision.get("action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvE0bDv1Error("E0B_CERT_BINDING_ACTION_MISMATCH")
    return {
        "certified_decision_result_hash": result_hash,
        "decision_id": decision["decision_id"],
        "portfolio_action": decision["action"],
        "certification_status": (component.get("certification") or {}).get(
            "certification_status"
        ),
        "rationale_ref": decision.get("rationale_ref"),
    }


def build_comparison(
    *,
    current_decision_path: Path | None = None,
) -> Mapping[str, Any]:
    """Full DV1 comparison bound to existing NO_POSITION certification."""

    bundle = sealed_adversarial_bundle()
    baseline = sealed_human_baseline(bundle=bundle)
    packet = build_godview_packet(bundle=bundle)
    post = sealed_post_packet_decision(bundle=bundle, packet=packet)
    cert = load_no_position_cert_binding(current_decision_path=current_decision_path)

    baseline_rubric = score_rubric(_rubric_scores_baseline())
    post_rubric = score_rubric(_rubric_scores_godview_post())
    item_deltas = {
        item: int(post_rubric["items"][item]) - int(baseline_rubric["items"][item])
        for item in RUBRIC_ITEMS
    }
    total_delta = int(post_rubric["total"]) - int(baseline_rubric["total"])

    comparison = _plain(
        {
            "case_id": CASE_ID,
            "stage_target": "ONE_CASE_DECISION_DELTA_OBSERVED",
            "acceptance_case": "G08",
            "score_claim": {
                "shipped_product_score": 39,
                "score_frozen": True,
                "alpha_claim": False,
                "general_effectiveness_claim": False,
            },
            "bundle_hash": bundle["bundle_hash"],
            "baseline_hash": baseline["baseline_hash"],
            "packet_hash": packet["packet_hash"],
            "post_packet_hash": post["post_packet_hash"],
            "baseline": {
                "action": baseline["action"],
                "rationale": baseline["rationale"],
                "missing_evidence": list(baseline["missing_evidence"]),
                "falsifiers": list(baseline["falsifiers"]),
                "rubric": baseline_rubric,
            },
            "godview_packet": {
                "run_state": packet["run_state"],
                "block_reason": packet["block_reason"],
                "research_action": packet["research_action"],
                "rationale": packet["rationale"],
                "contradictions": list(packet["contradictions"]),
                "falsifiers": list(packet["falsifiers"]),
            },
            "post_packet": {
                "action": post["action"],
                "portfolio_action": post["portfolio_action"],
                "rationale": post["rationale"],
                "missing_evidence": list(post["missing_evidence"]),
                "falsifiers": list(post["falsifiers"]),
                "rubric": post_rubric,
            },
            "delta": {
                "action_change": baseline["action"] != post["action"],
                "baseline_action": baseline["action"],
                "post_action": post["action"],
                "rubric_item_deltas": item_deltas,
                "total_score_difference": total_delta,
                "missing_evidence_delta": list(post["missing_evidence"]),
                "falsifier_delta": list(post["falsifiers"]),
            },
            "no_position_cert_binding": cert,
        }
    )
    comparison["comparison_hash"] = domain_hash(DOMAIN_COMPARISON, comparison)
    return _freeze(comparison)


def build_comparison_presentation(comparison: Mapping[str, Any]) -> Mapping[str, Any]:
    """Operator-visible rows: action / rationale / missing-evidence / falsifier delta."""

    rows = [
        {"label": "Case", "value": str(comparison["case_id"])},
        {"label": "AcceptanceCase", "value": "G08"},
        {
            "label": "GodViewRunState",
            "value": str(comparison["godview_packet"]["run_state"]),
        },
        {
            "label": "BlockReason",
            "value": str(comparison["godview_packet"]["block_reason"]),
        },
        {
            "label": "BaselineAction",
            "value": str(comparison["baseline"]["action"]),
        },
        {
            "label": "PostPacketAction",
            "value": str(comparison["post_packet"]["action"]),
        },
        {
            "label": "ActionChange",
            "value": "TRUE" if comparison["delta"]["action_change"] else "FALSE",
        },
        {
            "label": "RubricTotalDelta",
            "value": str(comparison["delta"]["total_score_difference"]),
        },
        {
            "label": "MissingEvidenceDelta",
            "value": ";".join(comparison["delta"]["missing_evidence_delta"]) or "NONE",
        },
        {
            "label": "FalsifierDelta",
            "value": ";".join(comparison["delta"]["falsifier_delta"]) or "NONE",
        },
        {
            "label": "BoundCertifiedResultHash",
            "value": str(
                comparison["no_position_cert_binding"]["certified_decision_result_hash"]
            ),
        },
        {
            "label": "ComparisonHash",
            "value": str(comparison["comparison_hash"]),
        },
        {"label": "AlphaClaim", "value": "FALSE"},
        {"label": "ShippedProductScore", "value": "39"},
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
    current_decision_path: Path | None = None,
) -> Mapping[str, Any]:
    """Injected-renderer presentation for one visible comparison."""

    model_src = (
        comparison
        if comparison is not None
        else build_comparison(current_decision_path=current_decision_path)
    )
    presentation = build_comparison_presentation(model_src)
    renderer.subheader(presentation["title"])
    renderer.table(list(presentation["rows"]))
    renderer.caption(
        "E0B-DV1 · G08 BLOCKED:CONTRADICTORY_INDISPENSABLE_EVIDENCE · "
        "score 39 frozen · no alpha · bound to existing NO_POSITION certification"
    )
    return presentation


__all__ = [
    "BLOCK_REASON",
    "CASE_ID",
    "EXPECTED_CERTIFIED_RESULT_HASH",
    "RUBRIC_ITEMS",
    "GvE0bDv1Error",
    "build_comparison",
    "build_comparison_presentation",
    "build_godview_packet",
    "load_no_position_cert_binding",
    "render_e0b_dv1_comparison",
    "score_rubric",
    "sealed_adversarial_bundle",
    "sealed_human_baseline",
    "sealed_post_packet_decision",
]
