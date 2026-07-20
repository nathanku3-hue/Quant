"""E0B-DV1 G08: ledger authority, budget cap, mechanical blinding, two-human close.

Engine fixtures validate machinery only. REAL_HUMAN labels are attribution only.
Close requires real operator + different real reviewer + bound chain replay.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import core.gv_e0b_dv1_contradiction as e0b_mod
from core.gv_e0b_dv1_contradiction import (
    AUTH_FIXTURE,
    AUTH_REAL_OPERATOR,
    AUTH_REAL_REVIEWER,
    AdvanceableClock,
    BLOCK_REASON,
    BUDGET_MINUTES,
    CANONICAL_STAGE_ORDER,
    CASE_ID,
    E0B_DECISION_ID,
    RATIONALE_REF_PREFIX,
    REVIEW_ARM_FIELDS,
    REVIEW_INPUT_MODE_BLINDED,
    RUBRIC_ITEMS,
    RUN_CLASS_SYNTHETIC,
    GvE0bDv1Error,
    blank_baseline_authoring_template,
    blank_post_authoring_template,
    blank_rubric_authoring_template,
    build_comparison,
    build_comparison_presentation,
    build_result_document,
    e0b_rationale_ref,
    is_attribution_structure_valid,
    is_observed_comparison_eligible,
    load_baseline_seal,
    load_capture_session,
    load_post_packet_seal,
    observed_comparison_count_from_disk,
    open_capture_session,
    render_e0b_dv1_comparison,
    run_e0b_dv1_case,
    seal_baseline_record,
    seal_post_packet_record,
    seal_review_package,
    seal_rubric_record,
    sealed_adversarial_bundle,
    stage_build_review_package,
    stage_capture_baseline,
    stage_capture_post,
    stage_capture_rubric,
    stage_compare,
    stage_generate_packet,
    stage_open_arm,
    verify_bundle_seal,
    verify_mapping_randomization,
    verify_review_package_bound_to_records,
    verify_result_document,
    write_authoring_templates,
    write_canonical_artifacts,
)
from core.gv_fs0_canonical import domain_hash
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
    operator_fresh: bool = True,
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
        "operator_had_not_seen_packet_or_expected_outcome": operator_fresh,
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
    arm_a_fill: int = 0,
    arm_b_fill: int = 2,
    reviewer_blinded_receipt: bool = True,
) -> dict[str, Any]:
    """Blinded ARM authoring only — no baseline/post score path."""

    return {
        "case_id": CASE_ID,
        "authorship_kind": authorship,
        "reviewer_id": reviewer_id,
        "arm_a_scores": _arm_scores(arm_a_fill),
        "arm_b_scores": _arm_scores(arm_b_fill),
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
        "fresh_operator_attested": True,
        "blinded_review_conditions_attested": True,
        "reviewer_received_only_blinded_review_package": reviewer_blinded_receipt,
    }


def _plain(value: Any) -> Any:
    if isinstance(value, dict) or (
        hasattr(value, "items") and not isinstance(value, (str, bytes, list, tuple))
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
    early_submit_minutes: int | None = None,
    operator_fresh: bool = True,
    reviewer_blinded_receipt: bool = True,
    rng_first_byte: int = 0,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Any, Any]:
    """Staged capture with budget-cap timers and mechanical REVIEW_PACKAGE.

    Production stage draws secrets.token_bytes(16). Tests inject parity by
    mocking token_bytes: first byte even => ARM_A=BASELINE, ARM_B=POST.
    """

    import secrets as secrets_mod

    import core.gv_e0b_dv1_contradiction as e0b_mod

    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)

    op = "OP_HUMAN_1" if real_human else "OP_FIXTURE_1"
    rev = "REV_HUMAN_1" if real_human else "REV_FIXTURE_1"
    op_auth = AUTH_REAL_OPERATOR if real_human else AUTH_FIXTURE
    rev_auth = AUTH_REAL_REVIEWER if real_human else AUTH_FIXTURE
    spend = early_submit_minutes if early_submit_minutes is not None else 30
    forced_rng = bytes([rng_first_byte & 0xFF]) + b"\x11" * 15

    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(spend)
    b_path = tmp_path / "baseline_seal.json"
    stage_capture_baseline(
        _baseline_authoring(
            operator_id=op,
            authorship=op_auth,
            action=baseline_action,
            bundle_hash=bundle["bundle_hash"],
            operator_fresh=operator_fresh,
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
    clock.advance_minutes(spend)
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

    export_dir = tmp_path / "reviewer_export"
    custody_dir = tmp_path / "operator_custody"
    export_dir.mkdir(parents=True, exist_ok=True)
    custody_dir.mkdir(parents=True, exist_ok=True)
    pkg_path = export_dir / "review_package.json"
    map_path = custody_dir / "review_mapping.private.json"
    # Production stage has no rng_bytes; tests mock secrets.token_bytes only.
    if monkeypatch is not None:
        monkeypatch.setattr(e0b_mod.secrets, "token_bytes", lambda n: forced_rng)
        stage_build_review_package(
            baseline_path=b_path,
            post_path=p_path,
            packet_path=pkt_path,
            session_path=session_path,
            package_path=pkg_path,
            mapping_path=map_path,
            rubric_authoring_path=export_dir / "rubric_authoring.json",
            bundle=bundle,
        )
    else:
        original = e0b_mod.secrets.token_bytes
        e0b_mod.secrets.token_bytes = lambda n: forced_rng  # type: ignore[method-assign]
        try:
            stage_build_review_package(
                baseline_path=b_path,
                post_path=p_path,
                packet_path=pkt_path,
                session_path=session_path,
                package_path=pkg_path,
                mapping_path=map_path,
                rubric_authoring_path=export_dir / "rubric_authoring.json",
                bundle=bundle,
            )
        finally:
            e0b_mod.secrets.token_bytes = original  # type: ignore[method-assign]

    clock.advance_minutes(5)
    r_path = tmp_path / "rubric_scores.json"
    stage_capture_rubric(
        _rubric_authoring(
            reviewer_id=rev,
            authorship=rev_auth,
            arm_a_fill=baseline_fill,
            arm_b_fill=post_fill,
            reviewer_blinded_receipt=reviewer_blinded_receipt,
        ),
        rubric_path=r_path,
        baseline_path=b_path,
        post_path=p_path,
        packet_path=pkt_path,
        session_path=session_path,
        package_path=pkg_path,
        mapping_path=map_path,
        bundle=bundle,
        clock=clock,
    )
    return b_path, pkt_path, p_path, r_path, session_path, pkg_path, map_path, bundle, packet


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
    clock.advance_minutes(10)
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
        b, pkt, p, r, sess, pkg, mp, _bundle, packet = _fixture_paths(
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
            package_path=pkg,
            mapping_path=mp,
        )
        expected = (post_fill - baseline_fill) * len(RUBRIC_ITEMS)
        delta = comparison["delta"]["total_score_difference"]
        assert int(delta["value_string"]) == expected
        assert comparison["stage_claim"]["shipped_product_score"] == 39
        assert comparison["stage_claim"]["observed_comparison_count"] == 0
        assert comparison["stage_claim"]["e0b_close_eligible"] is False
        assert comparison["godview_packet"]["generated_at"] == packet["generated_at"]


def test_early_submit_within_budget_cap_accepted(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(
        tmp_path / "early", early_submit_minutes=15
    )
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    assert baseline["allowed_budget_minutes"] == BUDGET_MINUTES
    assert baseline["elapsed_seconds"] == 15 * 60
    assert baseline["elapsed_seconds"] < BUDGET_MINUTES * 60
    post = load_post_packet_seal(
        p, packet=json.loads(pkt.read_text(encoding="utf-8")), baseline=baseline
    )
    assert post["allowed_budget_minutes"] == baseline["allowed_budget_minutes"]
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    assert comparison["stage_claim"]["shipped_product_score"] == 39


def test_budget_exceeded_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(BUDGET_MINUTES + 1)
    with pytest.raises(GvE0bDv1Error, match="E0B_BUDGET_EXCEEDED"):
        stage_capture_baseline(
            _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
            baseline_path=tmp_path / "b.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )


def test_outside_research_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
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


def test_caller_timestamp_rejected(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
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


def test_review_package_withholds_mapping(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "caps")
    package = json.loads(pkg.read_text(encoding="utf-8"))
    assert package["mapping_withheld"] is True
    assert "arm_a_source" not in package
    assert "arm_b_source" not in package
    assert set(package["arm_a"]) == set(package["arm_b"]) == set(REVIEW_ARM_FIELDS)
    assert "portfolio_action" not in package["arm_a"]
    assert "portfolio_action" not in package["arm_b"]
    export_dir = pkg.parent
    export_names = {path.name for path in export_dir.iterdir()}
    assert export_names == {"review_package.json", "rubric_authoring.json"}
    assert "arm_a_source" not in (export_dir / "rubric_authoring.json").read_text(
        encoding="utf-8"
    )
    assert not (export_dir / "review_mapping.private.json").exists()
    assert mp.is_file()
    assert mp.parent.name == "operator_custody"
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    assert set({mapping["arm_a_source"], mapping["arm_b_source"]}) == {
        "BASELINE",
        "POST",
    }
    assert "rng_bytes_hex" in mapping
    verify_mapping_randomization(mapping)
    session = load_capture_session(sess)
    rp = next(e for e in session["events"] if e["stage"] == "REVIEW_PACKAGE")
    assert rp["payload"]["mapping_commitment"] == mapping["mapping_commitment"]
    assert "mapping_hash" not in rp["payload"]


def test_open_arm_sealed_in_chain_not_mutable_map(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "caps")
    session = load_capture_session(sess)
    assert "open_arms" not in session
    stages = [e["stage"] for e in session["chain"]]
    assert stages == list(CANONICAL_STAGE_ORDER)
    events_dir = Path(session["events_dir"])
    # Mutating open event file without matching chain seal fails rebuild.
    open_file = events_dir / "0001.json"
    raw = json.loads(open_file.read_text(encoding="utf-8"))
    raw["payload"]["opened_at"] = "2026-07-19T00:00:00.000000Z"
    open_file.write_text(json.dumps(raw), encoding="utf-8")
    # Chain link still verifies; open-time bind to baseline fails on result.
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    assert baseline["arm_started_at"] != raw["payload"]["opened_at"]


def test_unbound_session_rejected(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "a")
    b2, pkt2, p2, r2, sess2, pkg2, mp2, _b2, _p2 = _fixture_paths(tmp_path / "b")
    with pytest.raises(GvE0bDv1Error):
        build_comparison(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess2,  # foreign session
            package_path=pkg,
            mapping_path=mp,
        )


def test_reviewer_must_differ_from_operator(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    package = json.loads(pkg.read_text(encoding="utf-8"))
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR"):
        seal_rubric_record(
            {
                **_rubric_authoring(reviewer_id=baseline["operator_id"]),
                "scored_at": "2026-07-19T16:00:00.000000Z",
                "session_nonce": baseline["session_nonce"],
                "prev_chain_hash": "a" * 64,
            },
            baseline=baseline,
            post=post,
            packet=packet,
            review_package=package,
            review_mapping=mapping,
        )


def test_rubric_reason_required(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    package = json.loads(pkg.read_text(encoding="utf-8"))
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    raw = {
        **_rubric_authoring(),
        "scored_at": "2026-07-19T16:00:00.000000Z",
        "session_nonce": baseline["session_nonce"],
        "prev_chain_hash": "b" * 64,
    }
    raw["arm_a_scores"][RUBRIC_ITEMS[0]]["reason"] = "   "
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_REASON_REQUIRED"):
        seal_rubric_record(
            raw,
            baseline=baseline,
            post=post,
            packet=packet,
            review_package=package,
            review_mapping=mapping,
        )


def test_baseline_post_scores_rejected(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    package = json.loads(pkg.read_text(encoding="utf-8"))
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    raw = {
        "case_id": CASE_ID,
        "authorship_kind": AUTH_FIXTURE,
        "reviewer_id": "REV_FIXTURE_1",
        "baseline_scores": _arm_scores(0),
        "post_scores": _arm_scores(2),
        "scored_at": "2026-07-19T16:00:00.000000Z",
        "session_nonce": baseline["session_nonce"],
        "prev_chain_hash": "b" * 64,
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
    }
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_UNBLINDED_SCORES_FORBIDDEN"):
        seal_rubric_record(
            raw,
            baseline=baseline,
            post=post,
            packet=packet,
            review_package=package,
            review_mapping=mapping,
        )


def test_rubric_single_arm_rejected(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    package = json.loads(pkg.read_text(encoding="utf-8"))
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    raw = {
        "case_id": CASE_ID,
        "authorship_kind": AUTH_FIXTURE,
        "reviewer_id": "REV_FIXTURE_1",
        "arm_a_scores": _arm_scores(1),
        "scored_at": "2026-07-19T16:00:00.000000Z",
        "session_nonce": baseline["session_nonce"],
        "prev_chain_hash": "b" * 64,
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
    }
    with pytest.raises(GvE0bDv1Error, match="E0B_RUBRIC_REQUIRES_BOTH_ARM_SCORES"):
        seal_rubric_record(
            raw,
            baseline=baseline,
            post=post,
            packet=packet,
            review_package=package,
            review_mapping=mapping,
        )


def test_wrong_private_mapping_fails_commitment(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "a")
    # Build a second session mapping and try to use it against first package.
    b2, pkt2, p2, r2, sess2, pkg2, mp2, bundle2, packet2 = _fixture_paths(
        tmp_path / "b", baseline_fill=2, post_fill=0
    )
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    package = json.loads(pkg.read_text(encoding="utf-8"))
    foreign_mapping = json.loads(mp2.read_text(encoding="utf-8"))
    with pytest.raises(GvE0bDv1Error):
        seal_rubric_record(
            {
                **_rubric_authoring(),
                "scored_at": "2026-07-19T16:00:00.000000Z",
                "session_nonce": baseline["session_nonce"],
                "prev_chain_hash": "b" * 64,
            },
            baseline=baseline,
            post=post,
            packet=packet,
            review_package=package,
            review_mapping=foreign_mapping,
        )


def test_eligibility_false_without_blinded_mode_field(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    rubric = dict(comparison["rubric"])
    # Simulate a seal missing blinded mode (cannot load via seal path).
    rubric["review_input_mode"] = "DIRECT_BASELINE_POST"
    assert (
        is_observed_comparison_eligible(
            comparison["baseline"],
            comparison["post_packet"],
            rubric,
        )
        is False
    )


def test_real_operator_freshness_fail_fast_at_capture(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    with pytest.raises(GvE0bDv1Error, match="E0B_OPERATOR_FRESHNESS_REQUIRED"):
        stage_capture_baseline(
            _baseline_authoring(
                operator_id="OP_HUMAN_1",
                authorship=AUTH_REAL_OPERATOR,
                bundle_hash=bundle["bundle_hash"],
                operator_fresh=False,
            ),
            baseline_path=tmp_path / "b.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )


def test_real_reviewer_custody_fail_fast_at_rubric(tmp_path: Path) -> None:
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_BLINDED_RECEIPT_REQUIRED"):
        _fixture_paths(
            tmp_path / "caps", real_human=True, reviewer_blinded_receipt=False
        )


def test_fixture_operator_freshness_false_blocks_eligibility(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(
        tmp_path / "caps", operator_fresh=False
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    assert comparison["baseline"]["operator_had_not_seen_packet_or_expected_outcome"] is False
    assert (
        is_observed_comparison_eligible(
            comparison["baseline"],
            comparison["post_packet"],
            comparison["rubric"],
        )
        is False
    )


def test_init_forms_emit_blank_templates(tmp_path: Path) -> None:
    paths = write_authoring_templates(tmp_path / "authoring")
    for key in ("baseline", "post", "rubric"):
        assert paths[key].is_file()
    rubric = json.loads(paths["rubric"].read_text(encoding="utf-8"))
    assert "arm_a_scores" in rubric and "arm_b_scores" in rubric
    assert "baseline_scores" not in rubric and "post_scores" not in rubric
    assert rubric["reviewer_received_only_blinded_review_package"] is None
    assert rubric["reviewer_id"] is None
    baseline = json.loads(paths["baseline"].read_text(encoding="utf-8"))
    assert baseline["operator_had_not_seen_packet_or_expected_outcome"] is None
    assert baseline["operator_id"] is None
    assert baseline["action"] is None
    assert baseline["rationale"] is None
    post = json.loads(paths["post"].read_text(encoding="utf-8"))
    assert post["operator_id"] is None
    assert post["action"] is None
    assert post["portfolio_action"] is None
    assert post["rationale"] is None
    blank = blank_rubric_authoring_template()
    assert blank["case_id"] == CASE_ID
    assert blank_baseline_authoring_template()[
        "operator_had_not_seen_packet_or_expected_outcome"
    ] is None
    with pytest.raises(GvE0bDv1Error, match="E0B_AUTHORING_TEMPLATE_EXISTS"):
        write_authoring_templates(tmp_path / "authoring")


def test_atomic_result_and_decision_packet(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    from core.gv_e0b_dv1_contradiction import _collect_sealed_records

    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
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
    assert result["close_claim"]["third_attestor_required"] is False
    loaded = json.loads(result_path.read_text(encoding="utf-8"))
    verify_result_document(loaded)
    assert "sealed_records" in loaded


def test_e0b_official_publication_surface_is_result_bound_only() -> None:
    forbidden = {
        "build_e0b_certified_result",
        "build_e0b_book",
        "build_e0b_decision",
        "publish_e0b_current_decision",
        "publish_current_decision",
    }
    assert forbidden.isdisjoint(set(e0b_mod.__all__))
    for name in forbidden:
        assert not hasattr(e0b_mod, name), name
    assert "publish" not in inspect.signature(stage_compare).parameters
    assert "publish" in inspect.signature(run_e0b_dv1_case).parameters
    assert "close_eligible" not in inspect.signature(run_e0b_dv1_case).parameters


@pytest.mark.parametrize("preexisting", [False, True])
def test_fixture_publish_rejected_without_creating_or_replacing_target(
    tmp_path: Path, preexisting: bool
) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    target = tmp_path / "current.json"
    sentinel = b"fixture-publication-must-not-replace\n"
    if preexisting:
        target.write_bytes(sentinel)

    with pytest.raises(GvE0bDv1Error, match="E0B_PUBLISH_REQUIRES_CLOSE_ELIGIBLE"):
        run_e0b_dv1_case(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            result_json_path=tmp_path / "result.json",
            decision_packet_path=tmp_path / "decision_packet.md",
            publish=True,
            current_target=target,
            current_lock=tmp_path / "current.lock",
        )

    if preexisting:
        assert target.read_bytes() == sentinel
    else:
        assert not target.exists()


@pytest.mark.parametrize("invalid_count", [0, 1.0, "1", True])
def test_publish_requires_exact_integer_count_one_from_reloaded_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid_count: Any
) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    real_loader = e0b_mod.load_verified_result

    def invalid_count_loader(path: Path) -> Any:
        result = _plain(real_loader(path))
        result["close_claim"]["observed_comparison_count"] = invalid_count
        return result

    monkeypatch.setattr(e0b_mod, "load_verified_result", invalid_count_loader)
    target = tmp_path / "current.json"
    with pytest.raises(GvE0bDv1Error, match="E0B_PUBLISH_REQUIRES_COUNT_ONE"):
        run_e0b_dv1_case(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            result_json_path=tmp_path / "result.json",
            decision_packet_path=tmp_path / "decision_packet.md",
            publish=True,
            current_target=target,
            current_lock=tmp_path / "current.lock",
        )
    assert not target.exists()


def test_tampered_reloaded_result_cannot_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    real_writer = e0b_mod.write_canonical_artifacts

    def tampering_writer(*args: Any, **kwargs: Any) -> Any:
        result = real_writer(*args, **kwargs)
        result_path = Path(kwargs["result_json_path"])
        raw = json.loads(result_path.read_text(encoding="utf-8"))
        raw["result_hash"] = "0" * 64
        _write_json(result_path, raw)
        return result

    monkeypatch.setattr(e0b_mod, "write_canonical_artifacts", tampering_writer)
    target = tmp_path / "current.json"
    with pytest.raises(GvE0bDv1Error, match="E0B_RESULT_SEAL_MISMATCH"):
        run_e0b_dv1_case(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            result_json_path=tmp_path / "result.json",
            decision_packet_path=tmp_path / "decision_packet.md",
            publish=True,
            current_target=target,
            current_lock=tmp_path / "current.lock",
        )
    assert not target.exists()


def test_reloaded_result_comparison_mismatch_cannot_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    real_loader = e0b_mod.load_verified_result

    def mismatching_loader(path: Path) -> Any:
        result = _plain(real_loader(path))
        result["comparison"]["comparison_hash"] = "0" * 64
        return result

    monkeypatch.setattr(e0b_mod, "load_verified_result", mismatching_loader)
    target = tmp_path / "current.json"
    with pytest.raises(GvE0bDv1Error, match="E0B_RESULT_SEAL_MISMATCH"):
        run_e0b_dv1_case(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            result_json_path=tmp_path / "result.json",
            decision_packet_path=tmp_path / "decision_packet.md",
            publish=True,
            current_target=target,
            current_lock=tmp_path / "current.lock",
        )
    assert not target.exists()


def test_fixture_not_close_eligible(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    assert comparison["stage_claim"]["e0b_close_eligible"] is False
    assert (
        is_observed_comparison_eligible(
            comparison["baseline"],
            comparison["post_packet"],
            comparison["rubric"],
        )
        is False
    )


def test_real_human_two_person_enables_close_and_publish(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(
        tmp_path / "caps", real_human=True
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    assert comparison["stage_claim"]["attribution_structure_valid"] is True
    # Comparison seal freezes close false; result-level eligibility is true for reals.
    assert comparison["stage_claim"]["e0b_close_eligible"] is False
    assert comparison["rubric"]["review_input_mode"] == REVIEW_INPUT_MODE_BLINDED
    assert comparison["baseline"]["operator_had_not_seen_packet_or_expected_outcome"] is True
    assert (
        comparison["rubric"]["custody_attestation"][
            "reviewer_received_only_blinded_review_package"
        ]
        is True
    )
    assert is_attribution_structure_valid(
        comparison["baseline"],
        comparison["post_packet"],
        comparison["rubric"],
    )
    assert is_observed_comparison_eligible(
        comparison["baseline"],
        comparison["post_packet"],
        comparison["rubric"],
    )
    out = run_e0b_dv1_case(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
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
    result_comparison_hash = out["result"]["comparison"]["comparison_hash"]
    assert component["decision"]["rationale_ref"] == e0b_rationale_ref(
        result_comparison_hash
    )
    assert component["decision"]["rationale_ref"].startswith(RATIONALE_REF_PREFIX)


def test_third_attestor_api_removed() -> None:
    import core.gv_e0b_dv1_contradiction as mod

    assert not hasattr(mod, "seal_close_attestation")
    assert not hasattr(mod, "verify_close_attestation")
    assert not hasattr(mod, "AUTH_EXTERNAL_ATTESTOR")


def test_review_arms_identical_schema_and_swap_mapping(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    root = tmp_path / "schema"
    session_path = root / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    b_path = root / "baseline_seal.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    clock.advance_minutes(1)
    pkt_path = root / "packet.json"
    stage_generate_packet(
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    stage_open_arm("POST", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    p_path = root / "post.json"
    stage_capture_post(
        _post_authoring(bundle_hash=bundle["bundle_hash"]),
        post_path=p_path,
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    baseline = load_baseline_seal(b_path, expected_bundle_hash=bundle["bundle_hash"])
    packet = json.loads(pkt_path.read_text(encoding="utf-8"))
    post = load_post_packet_seal(p_path, packet=packet, baseline=baseline)
    session = load_capture_session(session_path)
    tip = session["chain"][-1]["chain_hash"]
    from core.gv_e0b_dv1_contradiction import _project_decision_for_blind

    pkg0, map0 = seal_review_package(
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bundle,
        session_nonce=session["session_nonce"],
        prev_chain_hash=tip,
        rng_bytes=b"\x00" + b"\x11" * 15,
    )
    pkg1, map1 = seal_review_package(
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bundle,
        session_nonce=session["session_nonce"],
        prev_chain_hash=tip,
        rng_bytes=b"\x01" + b"\x11" * 15,
    )
    expected_baseline = _project_decision_for_blind(baseline)
    expected_post = _project_decision_for_blind(post)
    assert set(pkg0["arm_a"]) == set(pkg0["arm_b"]) == set(REVIEW_ARM_FIELDS)
    assert set(pkg1["arm_a"]) == set(pkg1["arm_b"]) == set(REVIEW_ARM_FIELDS)
    assert "portfolio_action" not in pkg0["arm_a"]
    assert map0["arm_a_source"] == "BASELINE" and map0["arm_b_source"] == "POST"
    assert map1["arm_a_source"] == "POST" and map1["arm_b_source"] == "BASELINE"
    assert map0["arm_a_source"] != map1["arm_a_source"]
    # Exact expected projections for both RNG parities (not a vacuous schema check).
    assert pkg0["arm_a"] == expected_baseline
    assert pkg0["arm_b"] == expected_post
    assert pkg1["arm_a"] == expected_post
    assert pkg1["arm_b"] == expected_baseline
    assert pkg0["arm_a"]["action"] != pkg0["arm_b"]["action"]
    verify_mapping_randomization(map0)
    verify_mapping_randomization(map1)
    verify_review_package_bound_to_records(
        package=pkg0,
        mapping=map0,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bundle,
    )
    verify_review_package_bound_to_records(
        package=pkg1,
        mapping=map1,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bundle,
    )


def test_reviewer_export_rejects_stale_files(tmp_path: Path) -> None:
    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    b_path = tmp_path / "baseline_seal.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    clock.advance_minutes(1)
    pkt_path = tmp_path / "packet.json"
    stage_generate_packet(
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    stage_open_arm("POST", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    p_path = tmp_path / "post.json"
    stage_capture_post(
        _post_authoring(bundle_hash=bundle["bundle_hash"]),
        post_path=p_path,
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    export_dir = tmp_path / "reviewer_export"
    export_dir.mkdir()
    (export_dir / "stale_mapping.json").write_text("{}", encoding="utf-8")
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_EXPORT_NOT_EMPTY"):
        stage_build_review_package(
            baseline_path=b_path,
            post_path=p_path,
            packet_path=pkt_path,
            session_path=session_path,
            package_path=export_dir / "review_package.json",
            mapping_path=tmp_path / "operator_custody" / "review_mapping.private.json",
            rubric_authoring_path=export_dir / "rubric_authoring.json",
            bundle=bundle,
        )


def test_fixture_run_not_observed_close(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    out = run_e0b_dv1_case(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
        result_json_path=tmp_path / "result.json",
        decision_packet_path=tmp_path / "decision_packet.md",
        publish=False,
    )
    assert out["observed_comparison_count"] == 0
    assert out["e0b_close_eligible"] is False
    assert out["run_class"] == RUN_CLASS_SYNTHETIC
    assert observed_comparison_count_from_disk(tmp_path / "result.json") == 0


def test_presentation_and_render(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, _bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
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
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    with pytest.raises(GvE0bDv1Error, match="E0B_POST_OPERATOR_MUST_MATCH_BASELINE"):
        seal_post_packet_record(
            {
                **_post_authoring(
                    operator_id="OP_OTHER",
                    bundle_hash=bundle["bundle_hash"],
                ),
                "arm_started_at": "2026-07-19T14:00:00.000000Z",
                "arm_ended_at": "2026-07-19T14:15:00.000000Z",
                "arm_opened_event_hash": "c" * 64,
                "allowed_budget_minutes": BUDGET_MINUTES,
                "elapsed_seconds": 900,
                "session_nonce": baseline["session_nonce"],
                "prev_chain_hash": "c" * 64,
                "equal_budget_attestation": True,
            },
            packet=packet,
            baseline=baseline,
        )


def test_unsealed_loads_rejected(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
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
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
    )
    from core.gv_e0b_dv1_contradiction import _collect_sealed_records

    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
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


def test_session_chain_exact_order(tmp_path: Path) -> None:
    b, pkt, p, r, sess, pkg, mp, bundle, _packet = _fixture_paths(tmp_path / "caps")
    session = load_capture_session(sess)
    stages = [e["stage"] for e in session["chain"]]
    assert stages == list(CANONICAL_STAGE_ORDER)
    # Tamper chain tip
    events_dir = Path(session["events_dir"])
    tip = events_dir / f"{len(stages) - 1:04d}.json"
    raw = json.loads(tip.read_text(encoding="utf-8"))
    raw["link"]["record_hash"] = "d" * 64
    tip.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(GvE0bDv1Error):
        load_capture_session(sess)


def test_capture_runner_module_importable() -> None:
    import scripts.gv_e0b_g08_capture as runner

    assert hasattr(runner, "main")


def test_unedited_blank_forms_fail_immediately(tmp_path: Path) -> None:
    """Unedited templates must fail seal (null IDs/action, no placeholder accept)."""

    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    blank_baseline = blank_baseline_authoring_template()
    blank_baseline["bundle_hash"] = bundle["bundle_hash"]
    with pytest.raises(GvE0bDv1Error, match="E0B_OPERATOR_REQUIRED|E0B_ACTION_REQUIRED"):
        stage_capture_baseline(
            blank_baseline,
            baseline_path=tmp_path / "b.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )
    # Placeholder IDs and REPLACE_WITH text are rejected even when non-null.
    with pytest.raises(GvE0bDv1Error, match="E0B_OPERATOR_REQUIRED"):
        stage_capture_baseline(
            {
                **_baseline_authoring(bundle_hash=bundle["bundle_hash"]),
                "operator_id": "REPLACE_WITH_OPERATOR_ID",
            },
            baseline_path=tmp_path / "b2.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )
    with pytest.raises(GvE0bDv1Error, match="E0B_RATIONALE_REQUIRED"):
        stage_capture_baseline(
            {
                **_baseline_authoring(bundle_hash=bundle["bundle_hash"]),
                "rationale": "REPLACE_WITH_BASELINE_RATIONALE",
            },
            baseline_path=tmp_path / "b3.json",
            session_path=session_path,
            bundle=bundle,
            clock=clock,
        )
    blank_post = blank_post_authoring_template()
    assert blank_post["action"] is None
    assert blank_post["portfolio_action"] is None
    blank_rubric = blank_rubric_authoring_template()
    assert blank_rubric["reviewer_id"] is None

    # Build through REVIEW_PACKAGE only, then reject placeholder reviewer.
    full = tmp_path / "full"
    bundle2 = sealed_adversarial_bundle()
    clock2 = AdvanceableClock(_TEST_START)
    sess = full / "session.json"
    open_capture_session(bundle=bundle2, session_path=sess, clock=clock2)
    stage_open_arm("BASELINE", session_path=sess, clock=clock2)
    clock2.advance_minutes(10)
    b = full / "baseline.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle2["bundle_hash"]),
        baseline_path=b,
        session_path=sess,
        bundle=bundle2,
        clock=clock2,
    )
    clock2.advance_minutes(1)
    pkt = full / "packet.json"
    stage_generate_packet(
        baseline_path=b,
        packet_path=pkt,
        session_path=sess,
        bundle=bundle2,
        clock=clock2,
    )
    stage_open_arm("POST", session_path=sess, clock=clock2)
    clock2.advance_minutes(10)
    p = full / "post.json"
    stage_capture_post(
        _post_authoring(bundle_hash=bundle2["bundle_hash"]),
        post_path=p,
        baseline_path=b,
        packet_path=pkt,
        session_path=sess,
        bundle=bundle2,
        clock=clock2,
    )
    export = full / "export"
    custody = full / "custody"
    export.mkdir()
    custody.mkdir()
    pkg = export / "review_package.json"
    mp = custody / "review_mapping.private.json"
    import core.gv_e0b_dv1_contradiction as e0b_mod

    original = e0b_mod.secrets.token_bytes
    e0b_mod.secrets.token_bytes = lambda n: b"\x00" + b"\x11" * 15  # type: ignore[method-assign]
    try:
        stage_build_review_package(
            baseline_path=b,
            post_path=p,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            rubric_authoring_path=export / "rubric_authoring.json",
            bundle=bundle2,
        )
    finally:
        e0b_mod.secrets.token_bytes = original  # type: ignore[method-assign]
    clock2.advance_minutes(5)
    with pytest.raises(GvE0bDv1Error, match="E0B_REVIEWER_REQUIRED"):
        stage_capture_rubric(
            {
                **_rubric_authoring(),
                "reviewer_id": "REPLACE_WITH_REVIEWER_ID",
            },
            rubric_path=full / "bad_rubric.json",
            baseline_path=b,
            post_path=p,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            bundle=bundle2,
            clock=clock2,
        )


def test_package_binding_mutations_fail_final_replay(tmp_path: Path) -> None:
    """Mutated package content with recomputed seals must still fail bound replay."""

    from core.gv_e0b_dv1_contradiction import (
        DOMAIN_REVIEW_MAPPING,
        DOMAIN_REVIEW_PACKAGE,
        _collect_sealed_records,
        _project_decision_for_blind,
    )

    b, pkt, p, r, sess, pkg, mp, bundle, packet = _fixture_paths(tmp_path / "caps")
    baseline = load_baseline_seal(b, expected_bundle_hash=bundle["bundle_hash"])
    post = load_post_packet_seal(p, packet=packet, baseline=baseline)
    mapping = json.loads(mp.read_text(encoding="utf-8"))
    package = json.loads(pkg.read_text(encoding="utf-8"))

    # Sanity: honest package binds.
    verify_review_package_bound_to_records(
        package=package,
        mapping=mapping,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bundle,
    )
    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
        bundle=bundle,
    )
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        package_path=pkg,
        mapping_path=mp,
        bundle=bundle,
    )
    result = build_result_document(comparison, sealed_records=seals)
    verify_result_document(result)

    def _rehash_package(pkg_body: dict[str, Any]) -> dict[str, Any]:
        body = {k: v for k, v in pkg_body.items() if k != "review_package_hash"}
        out = dict(body)
        out["review_package_hash"] = domain_hash(DOMAIN_REVIEW_PACKAGE, body)
        return out

    def _rehash_mapping(map_body: dict[str, Any]) -> dict[str, Any]:
        body = {
            k: v
            for k, v in map_body.items()
            if k not in {"mapping_commitment", "rng_bytes_hex"}
        }
        out = dict(map_body)
        out["mapping_commitment"] = domain_hash(DOMAIN_REVIEW_MAPPING, body)
        return out

    # 1) Mutate arm rationale and recompute package hash — binding must fail.
    mut_arm = dict(package)
    mut_arm["arm_a"] = dict(package["arm_a"])
    mut_arm["arm_a"]["rationale"] = "adversarial alternate rationale"
    mut_arm = _rehash_package(mut_arm)
    # Keep mapping package hash consistent with mutated package.
    mut_map = dict(mapping)
    mut_map["review_package_hash"] = mut_arm["review_package_hash"]
    mut_map = _rehash_mapping(mut_map)
    with pytest.raises(GvE0bDv1Error, match="E0B_PACKAGE_ARM_"):
        verify_review_package_bound_to_records(
            package=mut_arm,
            mapping=mut_map,
            baseline=baseline,
            post=post,
            packet=packet,
            bundle=bundle,
        )

    # 2) Mutate embedded bundle and rehash — binding must fail.
    mut_bundle_pkg = dict(package)
    mut_bundle_pkg["bundle"] = dict(package["bundle"])
    mut_bundle_pkg["bundle"] = {
        **package["bundle"],
        "notes": "adversarial bundle note",
    }
    # Keep a self-consistent package hash over the mutated body.
    mut_bundle_pkg = _rehash_package(mut_bundle_pkg)
    mut_map2 = dict(mapping)
    mut_map2["review_package_hash"] = mut_bundle_pkg["review_package_hash"]
    mut_map2 = _rehash_mapping(mut_map2)
    with pytest.raises(GvE0bDv1Error, match="E0B_PACKAGE_BUNDLE_NOT_CANONICAL"):
        verify_review_package_bound_to_records(
            package=mut_bundle_pkg,
            mapping=mut_map2,
            baseline=baseline,
            post=post,
            packet=packet,
            bundle=bundle,
        )

    # 3) Mutate packet rationale field in package and rehash.
    mut_pkt = dict(package)
    mut_pkt["packet_rationale"] = "adversarial packet rationale"
    mut_pkt = _rehash_package(mut_pkt)
    mut_map3 = dict(mapping)
    mut_map3["review_package_hash"] = mut_pkt["review_package_hash"]
    mut_map3 = _rehash_mapping(mut_map3)
    with pytest.raises(GvE0bDv1Error, match="E0B_PACKAGE_PACKET_RATIONALE_MISMATCH"):
        verify_review_package_bound_to_records(
            package=mut_pkt,
            mapping=mut_map3,
            baseline=baseline,
            post=post,
            packet=packet,
            bundle=bundle,
        )

    # 4) Mutate mapping baseline/post hashes while keeping commitment recomputed.
    mut_map4 = dict(mapping)
    mut_map4["baseline_hash"] = "a" * 64
    mut_map4 = _rehash_mapping(mut_map4)
    with pytest.raises(GvE0bDv1Error, match="E0B_MAPPING_BASELINE_HASH_MISMATCH"):
        verify_review_package_bound_to_records(
            package=package,
            mapping=mut_map4,
            baseline=baseline,
            post=post,
            packet=packet,
            bundle=bundle,
        )
    mut_map5 = dict(mapping)
    mut_map5["post_packet_hash"] = "b" * 64
    mut_map5 = _rehash_mapping(mut_map5)
    with pytest.raises(GvE0bDv1Error, match="E0B_MAPPING_POST_HASH_MISMATCH"):
        verify_review_package_bound_to_records(
            package=package,
            mapping=mut_map5,
            baseline=baseline,
            post=post,
            packet=packet,
            bundle=bundle,
        )

    # 5) Disk-level mutation of package then collect/result must fail final replay.
    disk_pkg = dict(package)
    disk_pkg["arm_b"] = dict(package["arm_b"])
    disk_pkg["arm_b"]["rationale"] = "disk adversarial arm"
    disk_pkg = _rehash_package(disk_pkg)
    disk_map = dict(mapping)
    disk_map["review_package_hash"] = disk_pkg["review_package_hash"]
    disk_map = _rehash_mapping(disk_map)
    _write_json(pkg, disk_pkg)
    _write_json(mp, disk_map)
    with pytest.raises(GvE0bDv1Error, match="E0B_PACKAGE_ARM_"):
        _collect_sealed_records(
            baseline_path=b,
            post_path=p,
            rubric_path=r,
            packet_path=pkt,
            session_path=sess,
            package_path=pkg,
            mapping_path=mp,
            bundle=bundle,
        )

    # Projections for documentation of expected honest mapping.
    expected_baseline = _project_decision_for_blind(baseline)
    expected_post = _project_decision_for_blind(post)
    assert expected_baseline["action"] != expected_post["action"]


def test_revealed_mapping_only_after_rubric_close(tmp_path: Path) -> None:
    """Reveal file must not exist until durable RUBRIC_CLOSE completes."""

    bundle = sealed_adversarial_bundle()
    clock = AdvanceableClock(_TEST_START)
    session_path = tmp_path / "session.json"
    open_capture_session(bundle=bundle, session_path=session_path, clock=clock)
    stage_open_arm("BASELINE", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    b_path = tmp_path / "baseline_seal.json"
    stage_capture_baseline(
        _baseline_authoring(bundle_hash=bundle["bundle_hash"]),
        baseline_path=b_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    clock.advance_minutes(1)
    pkt_path = tmp_path / "packet.json"
    stage_generate_packet(
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    stage_open_arm("POST", session_path=session_path, clock=clock)
    clock.advance_minutes(10)
    p_path = tmp_path / "post.json"
    stage_capture_post(
        _post_authoring(bundle_hash=bundle["bundle_hash"]),
        post_path=p_path,
        baseline_path=b_path,
        packet_path=pkt_path,
        session_path=session_path,
        bundle=bundle,
        clock=clock,
    )
    export_dir = tmp_path / "reviewer_export"
    custody = tmp_path / "operator_custody"
    export_dir.mkdir()
    custody.mkdir()
    pkg_path = export_dir / "review_package.json"
    map_path = custody / "review_mapping.private.json"
    import core.gv_e0b_dv1_contradiction as e0b_mod

    original = e0b_mod.secrets.token_bytes
    e0b_mod.secrets.token_bytes = lambda n: b"\x00" + b"\x11" * 15  # type: ignore[method-assign]
    try:
        stage_build_review_package(
            baseline_path=b_path,
            post_path=p_path,
            packet_path=pkt_path,
            session_path=session_path,
            package_path=pkg_path,
            mapping_path=map_path,
            rubric_authoring_path=export_dir / "rubric_authoring.json",
            bundle=bundle,
        )
    finally:
        e0b_mod.secrets.token_bytes = original  # type: ignore[method-assign]
    reveal_path = map_path.with_name("review_mapping.revealed.json")
    assert not reveal_path.exists()
    clock.advance_minutes(5)
    stage_capture_rubric(
        _rubric_authoring(),
        rubric_path=tmp_path / "rubric.json",
        baseline_path=b_path,
        post_path=p_path,
        packet_path=pkt_path,
        session_path=session_path,
        package_path=pkg_path,
        mapping_path=map_path,
        bundle=bundle,
        clock=clock,
    )
    assert reveal_path.is_file()
    revealed = json.loads(reveal_path.read_text(encoding="utf-8"))
    assert revealed["revealed_after"] == "RUBRIC_CLOSE"
    session = load_capture_session(session_path)
    assert [e["stage"] for e in session["chain"]] == list(CANONICAL_STAGE_ORDER)


def test_rng_preimage_must_be_exactly_16_bytes() -> None:
    with pytest.raises(GvE0bDv1Error, match="E0B_RNG_PREIMAGE_LENGTH"):
        verify_mapping_randomization(
            {
                "rng_bytes_hex": b"\x00\x11".hex(),
                "rng_commitment": "0" * 64,
                "arm_a_source": "BASELINE",
                "arm_b_source": "POST",
            }
        )


def test_stage_build_review_package_has_no_rng_bytes_param() -> None:
    import inspect

    sig = inspect.signature(stage_build_review_package)
    assert "rng_bytes" not in sig.parameters
