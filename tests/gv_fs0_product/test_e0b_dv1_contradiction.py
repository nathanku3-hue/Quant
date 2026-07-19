"""E0B-DV1 G08: capture authority, seal replay, attestation-gated close.

Engine fixtures validate machinery only. REAL_HUMAN labels are attribution only.
Close requires external independent attestation + full embedded seal replay.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.gv_e0b_dv1_contradiction import (
    AUTH_EXTERNAL_ATTESTOR,
    AUTH_FIXTURE,
    AUTH_REAL_OPERATOR,
    AUTH_REAL_REVIEWER,
    AdvanceableClock,
    BLOCK_REASON,
    BUDGET_MINUTES,
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
    is_attribution_structure_valid,
    is_observed_comparison_eligible,
    load_baseline_seal,
    load_post_packet_seal,
    load_rubric_scores,
    observed_comparison_count_from_disk,
    open_capture_session,
    publish_e0b_current_decision,
    render_e0b_dv1_comparison,
    run_e0b_dv1_case,
    seal_baseline_record,
    seal_close_attestation,
    seal_post_packet_record,
    seal_rubric_record,
    sealed_adversarial_bundle,
    stage_capture_baseline,
    stage_capture_post,
    stage_capture_rubric,
    stage_generate_packet,
    stage_open_arm,
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


def _baseline_authoring(
    *,
    operator_id: str = "OP_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    action: str = "ADVANCE_TO_FULL_RESEARCH",
    bundle_hash: str,
    contradictions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "arm": "HUMAN_BASELINE",
        "authorship_kind": authorship,
        "operator_id": operator_id,
        "bundle_hash": bundle_hash,
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


def _post_authoring(
    *,
    operator_id: str = "OP_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    action: str = "HOLD_FOR_EVIDENCE",
    bundle_hash: str,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "arm": "HUMAN_POST_PACKET",
        "authorship_kind": authorship,
        "operator_id": operator_id,
        "bundle_hash": bundle_hash,
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


def _rubric_authoring(
    *,
    reviewer_id: str = "REV_FIXTURE_1",
    authorship: str = AUTH_FIXTURE,
    baseline_fill: int = 0,
    post_fill: int = 2,
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "authorship_kind": authorship,
        "reviewer_id": reviewer_id,
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


_TEST_START = "2026-07-19T12:00:00.000000Z"


def _fixture_paths(
    tmp_path: Path,
    *,
    baseline_fill: int = 0,
    post_fill: int = 2,
    post_action: str = "HOLD_FOR_EVIDENCE",
    baseline_action: str = "ADVANCE_TO_FULL_RESEARCH",
    real_human: bool = False,
) -> tuple[Path, Path, Path, Path, Path, Any, Any]:
    """Staged capture with system-stamped 60m budgets via AdvanceableClock."""

    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)

    op = "OP_HUMAN_1" if real_human else "OP_FIXTURE_1"
    rev = "REV_HUMAN_1" if real_human else "REV_FIXTURE_1"
    op_auth = AUTH_REAL_OPERATOR if real_human else AUTH_FIXTURE
    rev_auth = AUTH_REAL_REVIEWER if real_human else AUTH_FIXTURE

    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    b_path = tmp_path / "baseline_seal.json"
    stage_capture_baseline(
        _baseline_authoring(
            operator_id=op,
            authorship=op_auth,
            action=baseline_action,
            bundle_hash=bundle["bundle_hash"],
        ),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )

    clock.advance_minutes(1)
    pkt_path = tmp_path / "packet.json"
    packet = stage_generate_packet(
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )

    stage_open_arm("POST", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    p_path = tmp_path / "post_packet_seal.json"
    stage_capture_post(
        _post_authoring(
            operator_id=op,
            authorship=op_auth,
            action=post_action,
            bundle_hash=bundle["bundle_hash"],
        ),
        post_path=p_path,
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )

    stage_open_arm("RUBRIC", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    r_path = tmp_path / "rubric_scores.json"
    stage_capture_rubric(
        _rubric_authoring(
            reviewer_id=rev,
            authorship=rev_auth,
            baseline_fill=baseline_fill,
            post_fill=post_fill,
        ),
        rubric_path=r_path,
        baseline_path=b_path,
        post_path=p_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    return b_path, pkt_path, p_path, r_path, session_path, bundle, packet


def _make_attestation(
    *,
    comparison_hash: str,
    operator_id: str,
    reviewer_id: str,
    session_nonce: str,
    attestor_id: str = "ATT_INDEPENDENT_1",
    attested_at: str = "2026-07-19T16:00:00.000000Z",
) -> Any:
    return seal_close_attestation(
        {
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
            "notes": "Independent attestation: fresh operator and blinded reviewer.",
        }
    )


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


def test_godview_packet_blocks_g08_without_average(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    b_path = tmp_path / "baseline.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    clock.advance_minutes(1)
    packet = stage_generate_packet(
        baseline_path=b_path,
        packet_path=tmp_path / "packet.json",
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    assert packet["run_state"] == "BLOCKED"
    assert packet["block_reason"] == BLOCK_REASON
    assert packet["run_class"] == RUN_CLASS_SYNTHETIC
    assert packet["engine_may_not_average"] is True
    values = packet["contradictions"][0]["values"]
    assert set(values) == {2, 8}
    assert 5 not in values


def test_packet_generated_at_not_hardcoded_calendar_day() -> None:
    import core.gv_e0b_dv1_contradiction as mod
    import inspect

    source = inspect.getsource(mod.build_godview_packet)
    assert "2026-07-19T12:30:00.000000Z" not in source


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
        b, pkt, p, r, sess, _bundle, packet = _fixture_paths(
            tmp_path / f"d{baseline_fill}{post_fill}",
            baseline_fill=baseline_fill,
            post_fill=post_fill,
        )
        comparison = build_comparison(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
        )
        expected = (post_fill - baseline_fill) * len(RUBRIC_ITEMS)
        delta = comparison["delta"]["total_score_difference"]
        assert int(delta["value_string"]) == expected
        assert comparison["stage_claim"]["shipped_product_score"] == 39
        assert comparison["stage_claim"]["observed_comparison_count"] == 0
        assert comparison["stage_claim"]["e0b_close_eligible"] is False
        assert comparison["godview_packet"]["generated_at"] == packet["generated_at"]


def test_baseline_after_packet_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    b_path = tmp_path / "baseline.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    clock.advance_minutes(1)
    packet = stage_generate_packet(
        baseline_path=b_path,
        packet_path=tmp_path / "packet.json",
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    # Manual late baseline body cannot satisfy ordering when re-sealed against packet.
    baseline = load_baseline_seal(b_path, expected_bundle_hash=bundle["bundle_hash"])
    late = dict(_plain(baseline))
    late["arm_started_at"] = "2026-07-19T14:00:00.000000Z"
    late["arm_ended_at"] = "2026-07-19T15:00:00.000000Z"
    late["sealed_at"] = late["arm_ended_at"]
    del late["baseline_hash"]
    late_sealed = seal_baseline_record(late)
    late_path = _write_json(tmp_path / "late.json", dict(late_sealed))
    with pytest.raises(GvE0bDv1Error, match="E0B_INVALID_BASELINE_SEAL"):
        build_comparison(
            baseline_path=late_path,
            post_path=late_path,
            rubric_path=late_path,
            packet=packet,
            bundle=bundle,
            session_path=session_path,
        )


def test_outside_research_and_unequal_budget_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    bad = _baseline_authoring(bundle_hash=bundle["bundle_hash"])
    bad["outside_research_attestation"] = True
    with pytest.raises(GvE0bDv1Error, match="E0B_OUTSIDE_RESEARCH_FORBIDDEN"):
        stage_capture_baseline(
            bad,
            baseline_path=tmp_path / "b.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )
    # Wrong budget: open arm and advance only 30 minutes.
    clock2 = AdvanceableClock(_TEST_START)
    session_path2 = tmp_path / "session2.json"
    open_capture_session(bundle=bundle, session_path=session_path2, clock=clock2)
    stage_open_arm("BASELINE", session_path=session_path2, clock=clock2)
    clock2.advance_minutes(30)
    with pytest.raises(GvE0bDv1Error, match="E0B_BUDGET_NOT_60"):
        stage_capture_baseline(
            _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
            baseline_path=tmp_path / "b2.json",
            session_path=session_path2,
            bundle=bundle,
            clock=clock2,
        )


def test_caller_timestamp_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES)
    bad = _baseline_authoring(bundle_hash=bundle["bundle_hash"])
    bad["sealed_at"] = "2026-07-19T12:10:00.000000Z"
    with pytest.raises(GvE0bDv1Error, match="E0B_CALLER_TIMING_FORBIDDEN"):
        stage_capture_baseline(
            bad,
            baseline_path=tmp_path / "b.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )


def test_reviewer_must_differ_from_operator(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR"):
        seal_rubric_record(
            {
                **_rubric_authoring(reviewer_id=baseline["operator_id"]),
                "arm_started_at": "2026-07-19T15:00:00.000000Z",
                "arm_ended_at": "2026-07-19T16:00:00.000000Z",
                "session_nonce": baseline["session_nonce"],
                "prev_chain_hash": "a" * 64,
            },
            baseline=baseline,
            post=post,
            packet=packet,
        )


def test_rubric_reason_required(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    raw = {
        **_rubric_authoring(),
        "arm_started_at": "2026-07-19T15:00:00.000000Z",
        "arm_ended_at": "2026-07-19T16:00:00.000000Z",
        "session_nonce": baseline["session_nonce"],
        "prev_chain_hash": "b" * 64,
    }
    raw["baseline_scores"][RUBRIC_ITEMS[0]]["reason"] = "   "
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_REASON_REQUIRED"):
        seal_rubric_record(raw, baseline=baseline, post=post, packet=packet)


def test_atomic_result_and_decision_packet(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    from core.gv_e0b_dv1_contradiction import _collect_sealed_records

    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        bundle=bundle,
    )
    result_path = tmp_path / "result.json"
    packet_path = tmp_path / "decision_packet.md"
    result = write_canonical_artifacts(
        comparison,
        sealed_records=seals,
        result_json_path=result_path,
        decision_packet_path=packet_path,
    )
    assert result_path.is_file()
    assert result["result_hash"]
    assert result["close_claim"]["observed_comparison_count"] == 0
    loaded = json.loads(result_path.read_text(encoding="utf-8"))
    verify_result_document(loaded)
    assert "sealed_records" in loaded


def test_e0b_cert_binds_comparison_hash(tmp_path: Path) -> None:
    b, pkt, p, r, sess, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    certified = build_e0b_certified_result(comparison)
    decision = certified["decision"]
    assert decision["decision_id"] == E0B_DECISION_ID
    assert decision["rationale_ref"] == e0b_rationale_ref(comparison["comparison_hash"])
    assert decision["rationale_ref"].startswith(RATIONALE_REF_PREFIX)


def test_fixture_publish_rejected_from_current_authority(tmp_path: Path) -> None:
    b, pkt, p, r, sess, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    with pytest.raises(GvE0bDv1Error, match="E0B_PUBLISH_REQUIRES_CLOSE_ELIGIBLE"):
        publish_e0b_current_decision(
            comparison, target=tmp_path / "c.json", lock_path=tmp_path / "c.lock"
        )


def test_real_human_labels_alone_not_close_eligible(tmp_path: Path) -> None:
    b, pkt, p, r, sess, _bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    assert comparison["stage_claim"]["attribution_structure_valid"] is True
    assert comparison["stage_claim"]["e0b_close_eligible"] is False
    assert comparison["stage_claim"]["observed_comparison_count"] == 0
    assert is_attribution_structure_valid(
        comparison["baseline"],
        comparison["post_packet"],
        comparison["rubric"],
    )
    assert (
        is_observed_comparison_eligible(
            comparison["baseline"],
            comparison["post_packet"],
            comparison["rubric"],
            comparison_hash=comparison["comparison_hash"],
        )
        is False
    )


def test_attestation_enables_close_and_publish(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    att = _make_attestation(
        comparison_hash=comparison["comparison_hash"],
        operator_id="OP_HUMAN_1",
        reviewer_id="REV_HUMAN_1",
        session_nonce=comparison["session_nonce"],
    )
    att_path = _write_json(tmp_path / "att.json", dict(att))
    out = run_e0b_dv1_case(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        attestation_path=att_path,
        result_json_path=tmp_path / "result.json",
        decision_packet_path=tmp_path / "decision_packet.md",
        publish=True,
        current_target=tmp_path / "current.json",
        current_lock=tmp_path / "current.lock",
    )
    assert out["e0b_close_eligible"] is True
    assert out["observed_comparison_count"] == 1
    assert observed_comparison_count_from_disk(tmp_path / "result.json") == 1
    component = parse_current_decision_bytes((tmp_path / "current.json").read_bytes())
    assert component["decision"]["decision_id"] == E0B_DECISION_ID


def test_fixture_run_not_observed_close(tmp_path: Path) -> None:
    b, pkt, p, r, sess, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    out = run_e0b_dv1_case(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        result_json_path=tmp_path / "result.json",
        decision_packet_path=tmp_path / "decision_packet.md",
        publish=False,
    )
    assert out["observed_comparison_count"] == 0
    assert out["e0b_close_eligible"] is False
    assert out["run_class"] == RUN_CLASS_SYNTHETIC
    assert observed_comparison_count_from_disk(tmp_path / "result.json") == 0


def test_presentation_and_render(tmp_path: Path) -> None:
    b, pkt, p, r, sess, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    presentation = build_comparison_presentation(comparison)
    rows = {row["label"]: row["value"] for row in presentation["rows"]}
    assert rows["BlockReason"] == BLOCK_REASON
    assert rows["ObservedComparisonCount"] == "0"
    assert rows["ShippedProductScore"] == "39"
    renderer = FakeRenderer()
    render_e0b_dv1_comparison(renderer, comparison=comparison)
    assert "observed-comparison count = 0" in renderer.calls[2][1]


def test_post_operator_must_match_baseline(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    with pytest.raises(GvE0bDv1Error, match="E0B_POST_OPERATOR_MUST_MATCH_BASELINE"):
        seal_post_packet_record(
            {
                **_post_authoring(
                    operator_id="OP_OTHER",
                    bundle_hash=bundle["bundle_hash"],
                ),
                "arm_started_at": "2026-07-19T14:00:00.000000Z",
                "arm_ended_at": "2026-07-19T15:00:00.000000Z",
                "session_nonce": baseline["session_nonce"],
                "prev_chain_hash": "c" * 64,
            },
            packet=packet,
            baseline=baseline,
        )


def test_unsealed_loads_rejected(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    unsealed = _baseline_authoring(bundle_hash=bundle["bundle_hash"])
    b_path = _write_json(tmp_path / "unsealed_baseline.json", unsealed)
    with pytest.raises(GvE0bDv1Error, match="E0B_BASELINE_UNSEALED"):
        load_baseline_seal(b_path, expected_bundle_hash=bundle["bundle_hash"])
    post_raw = _post_authoring(bundle_hash=bundle["bundle_hash"])
    p_path = _write_json(tmp_path / "unsealed_post.json", post_raw)
    with pytest.raises(GvE0bDv1Error, match="E0B_POST_UNSEALED"):
        load_post_packet_seal(p_path, packet=packet, baseline=baseline)


def test_mutated_observed_count_does_not_display(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    from core.gv_e0b_dv1_contradiction import _collect_sealed_records

    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        bundle=bundle,
    )
    result_path = tmp_path / "result.json"
    write_canonical_artifacts(
        comparison,
        sealed_records=seals,
        result_json_path=result_path,
        decision_packet_path=tmp_path / "decision_packet.md",
    )
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    raw["close_claim"]["observed_comparison_count"] = 7
    raw["close_claim"]["e0b_close_eligible"] = True
    result_path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    assert observed_comparison_count_from_disk(result_path) == 0
    with pytest.raises(GvE0bDv1Error):
        verify_result_document(raw)


def test_session_chain_append_only(tmp_path: Path) -> None:
    b, pkt, p, r, sess, bundle, _packet = _fixture_paths(tmp_path / "caps")
    from core.gv_e0b_dv1_contradiction import load_capture_session

    session = load_capture_session(sess)
    stages = [e["stage"] for e in session["chain"]]
    assert stages[0] == "SESSION_OPEN"
    assert "BASELINE" in stages
    assert "PACKET" in stages
    assert "POST" in stages
    assert "RUBRIC" in stages
    # Tamper chain tip
    session["chain"][-1]["record_hash"] = "d" * 64
    bad = tmp_path / "bad_session.json"
    _write_json(bad, session)
    with pytest.raises(GvE0bDv1Error):
        load_capture_session(bad)
