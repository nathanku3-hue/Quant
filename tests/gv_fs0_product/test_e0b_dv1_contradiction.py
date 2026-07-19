"""E0B-DV1 G08: external seals, hash recompute, artifacts, comparison-bound cert.

Engine fixtures validate machinery only. Real-human close eligibility is separate.
Positive, zero, and negative deltas are all protocol-valid.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.gv_e0b_dv1_contradiction import (
    AUTH_FIXTURE,
    AUTH_REAL_OPERATOR,
    AUTH_REAL_REVIEWER,
    BLOCK_REASON,
    CASE_ID,
    E0B_DECISION_ID,
    RATIONALE_REF_PREFIX,
    RUBRIC_ITEMS,
    RUN_CLASS_SYNTHETIC,
    GvE0bDv1Error,
    build_comparison,
    build_comparison_presentation,
    build_e0b_certified_result,
    build_godview_packet,
    e0b_rationale_ref,
    is_observed_comparison_eligible,
    load_baseline_seal,
    load_post_packet_seal,
    load_rubric_scores,
    observed_comparison_count_from_disk,
    publish_e0b_current_decision,
    render_e0b_dv1_comparison,
    run_e0b_dv1_case,
    seal_baseline_record,
    seal_post_packet_record,
    seal_rubric_record,
    sealed_adversarial_bundle,
    stage_capture_baseline,
    stage_generate_packet,
    verify_bundle_seal,
    verify_result_document,
    write_canonical_artifacts,
)
from core.gv_fs0_current_decision import parse_current_decision_bytes

ROOT = Path(__file__).resolve().parents[2]


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def _arm_scores(fill: int) -> dict[str, dict[str, Any]]:
    return {
        item: {"score": fill, "reason": f"fixture reason for {item}={fill}"}
        for item in RUBRIC_ITEMS
    }


def _baseline_raw(
    *,
    operator_id: str = "OP_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    action: str = "ADVANCE_TO_FULL_RESEARCH",
    sealed_at: str = "2026-07-19T12:10:00.000000Z",
    bundle_hash: str,
    contradictions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "arm": "HUMAN_BASELINE",
        "authorship_kind": authorship,
        "operator_id": operator_id,
        "sealed_at": sealed_at,
        "bundle_hash": bundle_hash,
        "human_analysis_time_minutes": 60,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "sealed_before_packet": True,
        "action": action,
        "rationale": "Fixture baseline rationale for engine tests only.",
        "missing_evidence": [],
        "falsifiers": [],
        "contradictions_recognized": list(contradictions or []),
        "alpha_claim": False,
    }


def _post_raw(
    *,
    operator_id: str = "OP_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    action: str = "HOLD_FOR_EVIDENCE",
    sealed_at: str = "2026-07-19T12:45:00.000000Z",
    bundle_hash: str,
    packet_hash: str,
    baseline_hash: str,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "arm": "HUMAN_POST_PACKET",
        "authorship_kind": authorship,
        "operator_id": operator_id,
        "sealed_at": sealed_at,
        "bundle_hash": bundle_hash,
        "packet_hash": packet_hash,
        "baseline_hash": baseline_hash,
        "human_analysis_time_minutes": 60,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "action": action,
        "portfolio_action": "NO_POSITION",
        "rationale": "Fixture post-packet rationale for engine tests only.",
        "missing_evidence": [
            "reconciled_point_in_time_qualified_sellable_supply_relief_path"
        ],
        "falsifiers": ["F_G08_INDISPENSABLE_CONTRADICTION"],
        "contradictions_recognized": [
            "qualified_sellable_supply_relief_quarters"
        ],
        "alpha_claim": False,
    }


def _rubric_raw(
    *,
    reviewer_id: str = "REV_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    baseline_fill: int = 0,
    post_fill: int = 2,
    scored_at: str = "2026-07-19T13:00:00.000000Z",
    bundle_hash: str,
    baseline_hash: str,
    packet_hash: str,
    post_packet_hash: str,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "authorship_kind": authorship,
        "reviewer_id": reviewer_id,
        "scored_at": scored_at,
        "bundle_hash": bundle_hash,
        "baseline_hash": baseline_hash,
        "packet_hash": packet_hash,
        "post_packet_hash": post_packet_hash,
        "baseline_scores": _arm_scores(baseline_fill),
        "post_scores": _arm_scores(post_fill),
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
    }


def _plain(value: Any) -> Any:
    if isinstance(value, dict) or hasattr(value, "items") and not isinstance(
        value, (str, bytes, list, tuple)
    ):
        try:
            return {str(k): _plain(v) for k, v in value.items()}  # type: ignore[union-attr]
        except Exception:
            pass
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_plain(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


# Deterministic stage timestamps for engine tests only (not production capture).
_TEST_BASELINE_AT = "2026-07-19T12:10:00.000000Z"
_TEST_PACKET_AT = "2026-07-19T12:30:00.000000Z"
_TEST_POST_AT = "2026-07-19T12:45:00.000000Z"
_TEST_RUBRIC_AT = "2026-07-19T13:00:00.000000Z"


def _fixture_paths(
    tmp_path: Path,
    *,
    baseline_fill: int = 0,
    post_fill: int = 2,
    post_action: str = "HOLD_FOR_EVIDENCE",
    baseline_action: str = "ADVANCE_TO_FULL_RESEARCH",
    real_human: bool = False,
) -> tuple[Path, Path, Path, Path, Any, Any]:
    """Return sealed baseline/packet/post/rubric paths + bundle + packet.

    Packet is generated *after* baseline with an explicit capture timestamp
    (tests inject fixed times for determinism; production uses wall-clock).
    """

    bundle = sealed_adversarial_bundle()
    op = "OP_HUMAN_1" if real_human else "OP_FIXTURE_1"
    rev = "REV_HUMAN_1" if real_human else "REV_FIXTURE_1"
    op_auth = AUTH_REAL_OPERATOR if real_human else AUTH_FIXTURE
    rev_auth = AUTH_REAL_REVIEWER if real_human else AUTH_FIXTURE
    baseline = seal_baseline_record(
        _baseline_raw(
            operator_id=op,
            authorship=op_auth,
            action=baseline_action,
            sealed_at=_TEST_BASELINE_AT,
            bundle_hash=bundle["bundle_hash"],
        )
    )
    # Stage order: baseline sealed first, then packet with actual capture time.
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    post = seal_post_packet_record(
        _post_raw(
            operator_id=op,
            authorship=op_auth,
            action=post_action,
            sealed_at=_TEST_POST_AT,
            bundle_hash=bundle["bundle_hash"],
            packet_hash=packet["packet_hash"],
            baseline_hash=baseline["baseline_hash"],
        ),
        packet=packet,
        baseline=baseline,
    )
    rubric = seal_rubric_record(
        _rubric_raw(
            reviewer_id=rev,
            authorship=rev_auth,
            baseline_fill=baseline_fill,
            post_fill=post_fill,
            scored_at=_TEST_RUBRIC_AT,
            bundle_hash=bundle["bundle_hash"],
            baseline_hash=baseline["baseline_hash"],
            packet_hash=packet["packet_hash"],
            post_packet_hash=post["post_packet_hash"],
        ),
        baseline=baseline,
        post=post,
        packet=packet,
    )
    b_path = _write_json(tmp_path / "baseline_seal.json", dict(baseline))
    pkt_path = _write_json(tmp_path / "packet.json", dict(packet))
    p_path = _write_json(tmp_path / "post_packet_seal.json", dict(post))
    r_path = _write_json(tmp_path / "rubric_scores.json", dict(rubric))
    return b_path, pkt_path, p_path, r_path, bundle, packet


def test_sealed_bundle_has_indispensable_contradiction() -> None:
    bundle = sealed_adversarial_bundle()
    assert bundle["case_id"] == CASE_ID
    claims = bundle["indispensable_claims"]
    assert len(claims) == 2
    assert claims[0]["value"] != claims[1]["value"]
    assert verify_bundle_seal(bundle) == bundle["bundle_hash"]


def test_bundle_tamper_under_claimed_hash_rejected() -> None:
    bundle = dict(sealed_adversarial_bundle())
    claimed = bundle["bundle_hash"]
    claims = list(bundle["indispensable_claims"])
    claims[0] = dict(claims[0])
    claims[0]["value"] = 99
    bundle["indispensable_claims"] = claims
    bundle["bundle_hash"] = claimed
    with pytest.raises(GvE0bDv1Error, match="E0B_BUNDLE_SEAL_MISMATCH"):
        verify_bundle_seal(bundle)


def test_godview_packet_blocks_g08_without_average() -> None:
    packet = build_godview_packet(generated_at=_TEST_PACKET_AT)
    assert packet["run_state"] == "BLOCKED"
    assert packet["block_reason"] == BLOCK_REASON
    assert packet["run_class"] == RUN_CLASS_SYNTHETIC
    assert packet["engine_may_not_average"] is True
    assert packet["generated_at"] == _TEST_PACKET_AT
    values = packet["contradictions"][0]["values"]
    assert set(values) == {2, 8}
    assert 5 not in values


def test_packet_generated_at_not_hardcoded_calendar_day() -> None:
    """Production default must capture wall-clock time, not a fixed day."""

    import core.gv_e0b_dv1_contradiction as mod
    import inspect

    source = inspect.getsource(mod.build_godview_packet)
    assert "2026-07-19T12:30:00.000000Z" not in source
    packet = build_godview_packet()
    assert packet["generated_at"].endswith("Z")
    assert len(packet["generated_at"]) == len("2026-07-19T12:30:00.000000Z")


def test_hardcoded_baseline_apis_removed() -> None:
    import core.gv_e0b_dv1_contradiction as mod

    for name in (
        "sealed_human_baseline",
        "sealed_post_packet_decision",
        "_rubric_scores_baseline",
        "_rubric_scores_godview_post",
    ):
        assert not hasattr(mod, name), f"hardcoded API still present: {name}"


def test_comparison_positive_zero_negative_deltas(tmp_path: Path) -> None:
    for baseline_fill, post_fill in ((0, 2), (1, 1), (2, 0)):
        b, pkt, p, r, _bundle, packet = _fixture_paths(
            tmp_path / f"d{baseline_fill}{post_fill}",
            baseline_fill=baseline_fill,
            post_fill=post_fill,
        )
        comparison = build_comparison(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
        )
        expected = (post_fill - baseline_fill) * len(RUBRIC_ITEMS)
        delta = comparison["delta"]["total_score_difference"]
        assert int(delta["value_string"]) == expected
        assert delta["magnitude"] == abs(expected)
        assert delta["is_negative"] is (expected < 0)
        assert comparison["stage_claim"]["shipped_product_score"] == 39
        assert comparison["stage_claim"]["observed_comparison_count"] == 0
        assert comparison["stage_claim"]["e0b_close_eligible"] is False
        assert comparison["stage_claim"]["causal_superiority_claim"] is False
        assert comparison["godview_packet"]["generated_at"] == packet["generated_at"]


def test_baseline_after_packet_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    baseline = seal_baseline_record(
        _baseline_raw(
            sealed_at="2026-07-19T12:40:00.000000Z",  # after packet 12:30
            bundle_hash=bundle["bundle_hash"],
        )
    )
    b_path = _write_json(tmp_path / "baseline.json", dict(baseline))
    with pytest.raises(GvE0bDv1Error, match="E0B_INVALID_BASELINE_SEAL_ORDERING"):
        seal_post_packet_record(
            _post_raw(
                sealed_at="2026-07-19T12:50:00.000000Z",
                bundle_hash=bundle["bundle_hash"],
                packet_hash=packet["packet_hash"],
                baseline_hash=baseline["baseline_hash"],
            ),
            packet=packet,
            baseline=baseline,
        )
    # Comparison entry also rejects late baseline before post/rubric load completes.
    with pytest.raises(GvE0bDv1Error, match="E0B_INVALID_BASELINE_SEAL"):
        build_comparison(
            baseline_path=b_path,
            post_path=b_path,
            rubric_path=b_path,
            packet=packet,
            bundle=bundle,
        )


def test_outside_research_and_unequal_budget_rejected() -> None:
    bundle = sealed_adversarial_bundle()
    bad = _baseline_raw(bundle_hash=bundle["bundle_hash"])
    bad["outside_research_attestation"] = True
    with pytest.raises(GvE0bDv1Error, match="E0B_OUTSIDE_RESEARCH_FORBIDDEN"):
        seal_baseline_record(bad)
    bad2 = _baseline_raw(bundle_hash=bundle["bundle_hash"])
    bad2["human_analysis_time_minutes"] = 30
    with pytest.raises(GvE0bDv1Error, match="E0B_UNEQUAL_BUDGET"):
        seal_baseline_record(bad2)


def test_reviewer_must_differ_from_operator(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    baseline = seal_baseline_record(
        _baseline_raw(operator_id="SAME_PERSON", bundle_hash=bundle["bundle_hash"])
    )
    post = seal_post_packet_record(
        _post_raw(
            operator_id="SAME_PERSON",
            bundle_hash=bundle["bundle_hash"],
            packet_hash=packet["packet_hash"],
            baseline_hash=baseline["baseline_hash"],
        ),
        packet=packet,
        baseline=baseline,
    )
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR"):
        seal_rubric_record(
            _rubric_raw(
                reviewer_id="SAME_PERSON",
                bundle_hash=bundle["bundle_hash"],
                baseline_hash=baseline["baseline_hash"],
                packet_hash=packet["packet_hash"],
                post_packet_hash=post["post_packet_hash"],
            ),
            baseline=baseline,
            post=post,
            packet=packet,
        )


def test_rubric_reason_required() -> None:
    bundle = sealed_adversarial_bundle()
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    baseline = seal_baseline_record(
        _baseline_raw(bundle_hash=bundle["bundle_hash"])
    )
    post = seal_post_packet_record(
        _post_raw(
            bundle_hash=bundle["bundle_hash"],
            packet_hash=packet["packet_hash"],
            baseline_hash=baseline["baseline_hash"],
        ),
        packet=packet,
        baseline=baseline,
    )
    raw = _rubric_raw(
        bundle_hash=bundle["bundle_hash"],
        baseline_hash=baseline["baseline_hash"],
        packet_hash=packet["packet_hash"],
        post_packet_hash=post["post_packet_hash"],
    )
    raw["baseline_scores"][RUBRIC_ITEMS[0]]["reason"] = "   "
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_REASON_REQUIRED"):
        seal_rubric_record(raw, baseline=baseline, post=post, packet=packet)


def test_atomic_result_and_decision_packet(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    result_path = tmp_path / "result.json"
    packet_path = tmp_path / "decision_packet.md"
    result = write_canonical_artifacts(
        comparison,
        result_json_path=result_path,
        decision_packet_path=packet_path,
    )
    assert result_path.is_file()
    assert packet_path.is_file()
    assert result["result_hash"]
    assert comparison["comparison_hash"] in packet_path.read_text(encoding="utf-8")
    loaded = json.loads(result_path.read_text(encoding="utf-8"))
    assert loaded["run_class"] == RUN_CLASS_SYNTHETIC
    assert loaded["comparison"]["comparison_hash"] == comparison["comparison_hash"]
    verify_result_document(loaded)


def test_e0b_cert_binds_comparison_hash(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    # Fixture cert remains test-only; publication is separately gated.
    certified = build_e0b_certified_result(comparison)
    decision = certified["decision"]
    assert decision["decision_id"] == E0B_DECISION_ID
    assert decision["rationale_ref"] == e0b_rationale_ref(comparison["comparison_hash"])
    assert decision["rationale_ref"].startswith(RATIONALE_REF_PREFIX)
    assert decision["action"] == "NO_POSITION"
    assert certified["certification"]["certification_status"] == "CERTIFIED"


def test_fixture_publish_rejected_from_current_authority(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    target = tmp_path / "current.json"
    lock = tmp_path / "current.lock"
    with pytest.raises(GvE0bDv1Error, match="E0B_PUBLISH_REQUIRES_CLOSE_ELIGIBLE"):
        publish_e0b_current_decision(comparison, target=target, lock_path=lock)
    assert not target.is_file()


def test_publish_close_eligible_current(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps", real_human=True)
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    assert comparison["stage_claim"]["e0b_close_eligible"] is True
    target = tmp_path / "current.json"
    lock = tmp_path / "current.lock"
    published = publish_e0b_current_decision(
        comparison, target=target, lock_path=lock
    )
    assert published.status == "PUBLISHED" or published.status
    component = parse_current_decision_bytes(target.read_bytes())
    assert component["decision"]["decision_id"] == E0B_DECISION_ID
    assert component["decision"]["rationale_ref"] == e0b_rationale_ref(
        comparison["comparison_hash"]
    )


def test_fixture_run_not_observed_close(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    out = run_e0b_dv1_case(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        result_json_path=tmp_path / "result.json",
        decision_packet_path=tmp_path / "decision_packet.md",
        publish=False,
    )
    assert out["observed_comparison_count"] == 0
    assert out["e0b_close_eligible"] is False
    assert out["run_class"] == RUN_CLASS_SYNTHETIC
    assert observed_comparison_count_from_disk(tmp_path / "result.json") == 0


def test_real_human_marks_observed_eligible(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps", real_human=True)
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    assert comparison["stage_claim"]["e0b_close_eligible"] is True
    assert comparison["stage_claim"]["observed_comparison_count"] == 1
    assert is_observed_comparison_eligible(
        comparison["baseline"],
        comparison["post_packet"],
        comparison["rubric"],
    )


def test_presentation_and_render(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    presentation = build_comparison_presentation(comparison)
    rows = {row["label"]: row["value"] for row in presentation["rows"]}
    assert rows["BlockReason"] == BLOCK_REASON
    assert rows["ObservedComparisonCount"] == "0"
    assert rows["ShippedProductScore"] == "39"
    assert rows["RunClass"] == RUN_CLASS_SYNTHETIC
    renderer = FakeRenderer()
    render_e0b_dv1_comparison(renderer, comparison=comparison)
    assert [name for name, _ in renderer.calls] == ["subheader", "table", "caption"]
    assert "observed-comparison count = 0" in renderer.calls[2][1]


def test_post_operator_must_match_baseline() -> None:
    bundle = sealed_adversarial_bundle()
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    baseline = seal_baseline_record(
        _baseline_raw(operator_id="OP_A", bundle_hash=bundle["bundle_hash"])
    )
    with pytest.raises(GvE0bDv1Error, match="E0B_POST_OPERATOR_MUST_MATCH_BASELINE"):
        seal_post_packet_record(
            _post_raw(
                operator_id="OP_B",
                bundle_hash=bundle["bundle_hash"],
                packet_hash=packet["packet_hash"],
                baseline_hash=baseline["baseline_hash"],
            ),
            packet=packet,
            baseline=baseline,
        )


def test_unsealed_loads_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    packet = build_godview_packet(bundle=bundle, generated_at=_TEST_PACKET_AT)
    baseline = seal_baseline_record(
        _baseline_raw(bundle_hash=bundle["bundle_hash"])
    )
    unsealed_b = _baseline_raw(bundle_hash=bundle["bundle_hash"])
    b_path = _write_json(tmp_path / "unsealed_baseline.json", unsealed_b)
    with pytest.raises(GvE0bDv1Error, match="E0B_BASELINE_UNSEALED"):
        load_baseline_seal(b_path, expected_bundle_hash=bundle["bundle_hash"])

    post_raw = _post_raw(
        bundle_hash=bundle["bundle_hash"],
        packet_hash=packet["packet_hash"],
        baseline_hash=baseline["baseline_hash"],
    )
    p_path = _write_json(tmp_path / "unsealed_post.json", post_raw)
    with pytest.raises(GvE0bDv1Error, match="E0B_POST_UNSEALED"):
        load_post_packet_seal(p_path, packet=packet, baseline=baseline)

    post = seal_post_packet_record(post_raw, packet=packet, baseline=baseline)
    rubric_raw = _rubric_raw(
        bundle_hash=bundle["bundle_hash"],
        baseline_hash=baseline["baseline_hash"],
        packet_hash=packet["packet_hash"],
        post_packet_hash=post["post_packet_hash"],
    )
    r_path = _write_json(tmp_path / "unsealed_rubric.json", rubric_raw)
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_UNSEALED"):
        load_rubric_scores(r_path, baseline=baseline, post=post, packet=packet)


def test_mutated_observed_count_does_not_display(tmp_path: Path) -> None:
    b, pkt, p, r, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b, post_path=p, rubric_path=r, packet_path=pkt
    )
    result_path = tmp_path / "result.json"
    write_canonical_artifacts(
        comparison,
        result_json_path=result_path,
        decision_packet_path=tmp_path / "decision_packet.md",
    )
    # Mutate displayed count without a valid result hash — must not inflate count.
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    raw["comparison"]["stage_claim"]["observed_comparison_count"] = 7
    raw["comparison"]["stage_claim"]["e0b_close_eligible"] = True
    result_path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    assert observed_comparison_count_from_disk(result_path) == 0
    with pytest.raises(GvE0bDv1Error):
        verify_result_document(raw)


def test_staged_pipeline_packet_after_baseline(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    b_path = tmp_path / "baseline_seal.json"
    pkt_path = tmp_path / "packet.json"
    stage_capture_baseline(
        _baseline_raw(
            sealed_at=_TEST_BASELINE_AT,
            bundle_hash=bundle["bundle_hash"],
        ),
        baseline_path=b_path,
        bundle=bundle,
    )
    packet = stage_generate_packet(
        baseline_path=b_path,
        packet_path=pkt_path,
        bundle=bundle,
        generated_at=_TEST_PACKET_AT,
    )
    assert packet["generated_at"] == _TEST_PACKET_AT
    assert pkt_path.is_file()
    # Packet before baseline seal time is rejected.
    with pytest.raises(GvE0bDv1Error, match="E0B_PACKET_MUST_FOLLOW_BASELINE"):
        stage_generate_packet(
            baseline_path=b_path,
            packet_path=tmp_path / "packet_bad.json",
            bundle=bundle,
            generated_at="2026-07-19T12:00:00.000000Z",
        )
