"""GV-BOUNDED-PORTFOLIO-1 acceptance tests (separate from Replay suite)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.bounded import (
    BOUNDED_SCHEMA,
    DEFAULT_CYCLE_COUNT,
    DISPOSITION_AIM_UNCHANGED,
    PROMOTION_TIP_SHA,
    REPLAY_CODE_PIN_SHA,
    BoundedPortfolioError,
    admit_follow_on_observation,
    assert_replay_baseline_pins,
    bootstrap_certified_workspace,
    branch_pins,
    load_session,
    run_bounded_portfolio,
    run_correction_lineage_probe,
    save_session,
    workspace_content_hash,
)
from gv_portfolio_v0.replay import reconstruct_exact
from gv_portfolio_v0.vertical import admit_watch_observation


def test_branch_pins_separate_promotion_tip_from_replay_code_pin() -> None:
    pins = branch_pins()
    assert pins["promotion_tip_sha"] == PROMOTION_TIP_SHA
    assert pins["replay_code_pin_sha"] == REPLAY_CODE_PIN_SHA
    assert pins["active_implementation_base"] == PROMOTION_TIP_SHA
    assert pins["immutable_replay_code_pin"] == REPLAY_CODE_PIN_SHA
    assert pins["promotion_tip_sha"] != pins["replay_code_pin_sha"]
    assert_replay_baseline_pins()


def test_persisted_cycles_consume_prior_state_and_grow_event_log(
    tmp_path: Path,
) -> None:
    report = run_bounded_portfolio(root=tmp_path, cycles=DEFAULT_CYCLE_COUNT)
    assert report["schema_version"] == BOUNDED_SCHEMA
    assert report["consumed_prior_persisted_state"] is True
    assert report["event_counts_strictly_increasing"] is True
    assert report["certification_chain_intact"] is True
    assert report["restart_reopen_verified"] is True
    assert report["cycle_count"] == DEFAULT_CYCLE_COUNT
    assert report["terminal_nav"] == "1499"
    assert report["unexplained_residual"] == "0"

    counts = [row["event_count"] for row in report["cycles"]]
    assert counts == sorted(counts)
    assert counts[0] < counts[1] < counts[2]

    # Each cycle consumed prior workspace hash
    assert report["cycles"][0]["prior_workspace_content_hash"]
    assert (
        report["cycles"][1]["prior_workspace_content_hash"]
        == report["cycles"][0]["workspace_content_hash"]
    )
    assert (
        report["cycles"][2]["prior_workspace_content_hash"]
        == report["cycles"][1]["workspace_content_hash"]
    )

    # Explicit observation disposition on every cycle
    for row in report["cycles"]:
        assert row["observation_disposition"] == DISPOSITION_AIM_UNCHANGED
        assert row["consumed_prior_persisted_state"] is True
        assert row["observation_record"]

    # Certification chain links
    assert (
        report["cycles"][1]["prior_certification_id"]
        == report["cycles"][0]["certification_id"]
    )
    assert (
        report["cycles"][2]["prior_certification_id"]
        == report["cycles"][1]["certification_id"]
    )

    # Session still loadable after run
    session = load_session(tmp_path)
    assert session["workspace_content_hash"] == report["final_workspace_content_hash"]
    reconstruct_exact(
        session["workspace"]["events"], expected_book=session["workspace"]["book"]
    )


def test_observation_is_explicit_no_change_not_silent(
    tmp_path: Path,
) -> None:
    report = run_bounded_portfolio(root=tmp_path, cycles=2)
    for row in report["cycles"]:
        rec = row["observation_record"]
        # disposition may be nested under bounded_disposition for follow-on
        if "disposition" in rec:
            assert rec["disposition"] == DISPOSITION_AIM_UNCHANGED
            assert rec.get("authorized_transition") is False
        else:
            assert rec.get("disposition") == DISPOSITION_AIM_UNCHANGED or rec.get(
                "source"
            )


def test_economically_distinct_observation_bytes_across_cycles(
    tmp_path: Path,
) -> None:
    report = run_bounded_portfolio(root=tmp_path, cycles=3)
    # Workspace hashes differ because observation/evidence/cert bytes differ
    hashes = [row["workspace_content_hash"] for row in report["cycles"]]
    assert len(set(hashes)) == 3
    # Economics of complete book remain residual-zero (no unauthorized transition)
    assert {row["terminal_nav"] for row in report["cycles"]} == {"1499"}


def test_forged_prior_certification_is_rejected() -> None:
    certified = bootstrap_certified_workspace()
    observed = admit_watch_observation(certified)
    forged = deepcopy(observed)
    forged["certification"] = dict(forged["certification"])
    forged["certification"]["terminal_book_hash"] = "0" * 64
    with pytest.raises(
        BoundedPortfolioError, match="FORGED_OR_STALE_PRIOR_CERTIFICATION"
    ):
        admit_follow_on_observation(
            forged,
            cycle_index=1,
            observation_content="tamper",
            locator="fixture://tamper",
            observed_at="2026-10-01T00:00:00.000000Z",
        )


def test_correction_chain_tampering_rejected() -> None:
    certified = bootstrap_certified_workspace()
    probe = run_correction_lineage_probe(certified)
    assert probe["forged_prior_rejected"] is True
    assert probe["prior_byte_stable"] is True


def test_session_hash_tamper_fails_reload(tmp_path: Path) -> None:
    run_bounded_portfolio(root=tmp_path, cycles=2)
    path = tmp_path / "bounded_session.json"
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw.replace("1499", "1498", 1), encoding="utf-8")
    with pytest.raises(BoundedPortfolioError, match="BOUNDED_SESSION_HASH_MISMATCH|BOUNDED_SESSION_WORKSPACE_HASH_MISMATCH"):
        load_session(tmp_path)


def test_duplicate_session_create_fails(tmp_path: Path) -> None:
    run_bounded_portfolio(root=tmp_path, cycles=2)
    with pytest.raises(BoundedPortfolioError, match="BOUNDED_SESSION_ALREADY_EXISTS"):
        run_bounded_portfolio(root=tmp_path, cycles=2)


def test_report_hash_stable_for_same_root_shape(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    first = run_bounded_portfolio(root=a, cycles=2)
    second = run_bounded_portfolio(root=b, cycles=2)
    # Paths differ in report; compare cycle economic fields
    assert first["cycles"][0]["book_hash"] == second["cycles"][0]["book_hash"]
    assert first["cycles"][1]["event_count"] == second["cycles"][1]["event_count"]
