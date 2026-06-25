import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m6_pit_walk_forward_equity_curve as strict_m6
from scripts import pead_m6b_bestavail_illustrative_2015_2019 as bestavail


def test_bestavail_claim_ceiling_flags_are_hard_locked() -> None:
    assert bestavail.CLAIM_CEILING_FLAGS == [
        "illustrative_only",
        "restated_vintage",
        "no_delisting",
        "survivorship_biased",
        "coverage_2015_2019",
        "provider_limited",
        "not_alpha",
        "not_tradable_claim",
    ]
    flags = bestavail.bestavail_validity_flags()
    for flag in bestavail.CLAIM_CEILING_FLAGS:
        assert flags[flag] is True
    assert flags["m6b_strict_readiness"] is False
    assert flags["usable_for_alpha_inference"] is False
    assert flags["no_delisting_adjustment"] is True
    assert flags["coverage_start"] == "2015-01-01"
    assert flags["coverage_end"] == "2019-12-31"


def test_bestavail_artifact_is_not_read_by_strict_m6_or_alpha_path() -> None:
    needle = bestavail.BESTAVAIL_EVIDENCE_PATH.name
    strict_paths = [
        Path(strict_m6.__file__),
        bestavail.ROOT / "scripts" / "pead_m5a_net_multifactor_alpha_test.py",
    ]
    for path in strict_paths:
        assert needle not in path.read_text(encoding="utf-8")
    assert bestavail.BESTAVAIL_EVIDENCE_PATH != strict_m6.OUTPUT_PATH
    assert bestavail.BESTAVAIL_DAILY_RETURNS_PATH != strict_m6.DAILY_RETURNS_OUTPUT_PATH


def test_direct_script_invocation_reaches_argparse_help() -> None:
    result = subprocess.run(
        [sys.executable, str(bestavail.ROOT / "scripts" / "pead_m6b_bestavail_illustrative_2015_2019.py"), "--help"],
        cwd=bestavail.ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--commit-bestavail-run" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr


def test_full_holding_window_filter_removes_terminal_events_before_engine() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["early_1", "early_2", "early_3", "early_4", "late_1", "late_2", "late_3", "late_4"],
            "security_id": ["A", "B", "C", "D", "A", "B", "C", "D"],
            "decision_date": ["2020-01-02"] * 4 + ["2020-01-09"] * 4,
            "signal": [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0],
            "tradable": [True] * 8,
            "liquidity_pass": [True] * 8,
        }
    )
    returns = pd.DataFrame(
        {
            "security_id": [security for security in ["A", "B", "C", "D"] for _ in range(8)],
            "return_date": list(pd.date_range("2020-01-03", periods=8, freq="D")) * 4,
            "tradable_total_return": [0.001] * 32,
        }
    )
    cfg = strict_m6.PortfolioConfig(holding_period_sessions=3, min_leg_count=1)

    filtered, metadata = bestavail.filter_events_for_full_holding_window(events, returns, cfg)
    assert metadata["events_removed_by_full_window_filter"] == 4
    assert set(filtered["event_id"]) == {"early_1", "early_2", "early_3", "early_4"}

    selected, _input_returns, calendar = strict_m6._prepare_sparse_engine_relations(filtered, returns, cfg)
    assert not selected.empty
    assert int((selected["exit_idx"] > int(calendar["return_idx"].max())).sum()) == 0


def test_bestavail_package_commit_rolls_back_if_second_replace_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    daily_path = tmp_path / "daily.parquet"
    evidence_path = tmp_path / "evidence.json"
    old_daily = b"old daily content"
    old_evidence = "old evidence content"
    daily_path.write_bytes(old_daily)
    evidence_path.write_text(old_evidence, encoding="utf-8")
    daily = pd.DataFrame(
        {
            "return_date": pd.to_datetime(["2020-01-03"]),
            "daily_gross_return": [0.001],
            "long_leg_contribution": [0.001],
            "short_leg_contribution": [0.0],
            "average_gross_exposure": [1.0],
            "average_net_exposure": [0.0],
            "short_exposure": [0.5],
            "active_names": [2],
            "turnover": [1.0],
            "turnover_cost": [0.0001],
            "short_borrow_cost": [0.0],
            "daily_net_return": [0.0009],
        }
    )
    evidence = {"schema_version": "test", "artifact_name": "bestavail_atomic_test"}
    real_replace = bestavail.os.replace

    def flaky_replace(src: object, dst: object) -> None:
        dst_path = Path(dst)
        src_path = Path(src)
        if dst_path == evidence_path and src_path.name.startswith(f".{evidence_path.name}.") and src_path.suffix == ".tmp":
            raise RuntimeError("simulated JSON commit failure")
        real_replace(src, dst)

    monkeypatch.setattr(bestavail.os, "replace", flaky_replace)
    with pytest.raises(RuntimeError, match="simulated JSON commit failure"):
        bestavail._commit_bestavail_outputs(daily, evidence, daily_returns_path=daily_path, evidence_path=evidence_path)

    assert daily_path.read_bytes() == old_daily
    assert evidence_path.read_text(encoding="utf-8") == old_evidence
