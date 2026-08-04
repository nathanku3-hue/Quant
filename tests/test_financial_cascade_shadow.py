from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_financial_cascade_shadow import main as cascade_cli_main
from research.financial_cascade_shadow import (
    CascadePromotionThresholds,
    StressWindow,
    run_financial_cascade_shadow,
)
from strategies.financial_cascade import (
    CascadeRiskState,
    FinancialCascadeError,
    FinancialCascadeObservation,
    FinancialCascadePolicy,
    apply_financial_cascade_cap,
    build_financial_cascade_overlay,
    classify_financial_cascade,
    load_verified_leningrad_bundle,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_file(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _identity(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _rational(value: Fraction | int) -> dict[str, int]:
    number = Fraction(value)
    return {"numerator": number.numerator, "denominator": number.denominator}


def _outcome(defaults: list[str], unpaid: Fraction | int) -> dict[str, object]:
    return {
        "accounting_invariants": {
            "payment_bounds": True,
            "fixed_point_equations": True,
            "outgoing_allocation": True,
            "non_negative_equity": True,
            "non_negative_unpaid_obligations": True,
            "all_pass": True,
        },
        "default_count": len(defaults),
        "defaults": defaults,
        "total_unpaid_obligations": _rational(unpaid),
    }


def _clearing(
    *,
    scenario_identity: str,
    state_name: str,
    defaults: list[str],
    unpaid: Fraction | int,
    non_unique: bool = False,
) -> dict[str, object]:
    nominal = {"A": _rational(10), "B": _rational(8), "C": _rational(4)}
    return {
        "schema_version": "finance-clearing-result-v1",
        "state_name": state_name,
        "scenario_identity": scenario_identity,
        "nominal_obligations": nominal,
        "non_unique": non_unique,
        "least": _outcome(defaults, unpaid),
        "greatest": _outcome(defaults, unpaid),
    }


def _write_bundle(
    root: Path,
    *,
    scenario_id: str,
    shock_defaults: list[str],
    shock_unpaid: Fraction | int,
    preferred: str | None = "inject-A",
    non_unique_states: list[str] | None = None,
) -> tuple[Path, str]:
    scenario = {
        "schema_version": "finance-intervention-choice-scenario-v2",
        "scenario_id": scenario_id,
        "institutions": [
            {
                "institution_id": "A",
                "external_assets": _rational(10),
                "outside_obligations": _rational(4),
            },
            {
                "institution_id": "B",
                "external_assets": _rational(2),
                "outside_obligations": _rational(3),
            },
            {
                "institution_id": "C",
                "external_assets": _rational(0),
                "outside_obligations": _rational(4),
            },
        ],
        "liabilities": [
            {"debtor": "A", "creditor": "B", "amount": _rational(6)},
            {"debtor": "B", "creditor": "C", "amount": _rational(5)},
        ],
        "shock": {"asset_reductions": {"A": _rational(6)}},
        "intervention_budget": _rational(6),
        "candidate_interventions": [
            {
                "intervention_id": "inject-A",
                "cash_injections": {"A": _rational(6)},
                "total_cost": _rational(6),
            },
            {
                "intervention_id": "inject-B",
                "cash_injections": {"B": _rational(6)},
                "total_cost": _rational(6),
            },
        ],
    }
    scenario_identity = _identity(
        {
            "kind": "finance-intervention-choice-scenario-identity-v2",
            "definition": scenario,
        }
    )
    baseline = _clearing(
        scenario_identity=scenario_identity,
        state_name="baseline",
        defaults=[],
        unpaid=0,
    )
    shock = _clearing(
        scenario_identity=scenario_identity,
        state_name="shock",
        defaults=shock_defaults,
        unpaid=shock_unpaid,
        non_unique="shock" in (non_unique_states or []),
    )
    candidates = {
        candidate_id: {
            "intervention_id": candidate_id,
            "clearing": _clearing(
                scenario_identity=scenario_identity,
                state_name=f"shock_plus_{candidate_id}",
                defaults=[],
                unpaid=0,
            ),
        }
        for candidate_id in ("inject-A", "inject-B")
    }
    comparison = {
        "schema_version": "finance-intervention-choice-comparison-v2",
        "scenario_identity": scenario_identity,
        "scenario_id": scenario_id,
        "baseline": baseline,
        "shock": shock,
        "candidates": candidates,
        "ranking_stable_across_extrema": True,
        "decision": "candidate_preferred" if preferred else "tie",
        "preferred_intervention_id": preferred,
        "non_unique_states": list(non_unique_states or []),
    }
    report = f"Synthetic source-oracle fixture for {scenario_id}.\n".encode("utf-8")

    root.mkdir()
    (root / "scenario.json").write_bytes(_canonical_file(scenario))
    (root / "comparison.json").write_bytes(_canonical_file(comparison))
    (root / "report.md").write_bytes(report)
    payload_hashes = {
        "scenario.json": sha256((root / "scenario.json").read_bytes()).hexdigest(),
        "comparison.json": sha256((root / "comparison.json").read_bytes()).hexdigest(),
        "report.md": sha256(report).hexdigest(),
    }
    bundle_identity = _identity(
        {
            "kind": "finance-intervention-choice-bundle-identity-v2",
            "payload_hashes": payload_hashes,
        }
    )
    index = {
        "schema_version": "finance-intervention-choice-bundle-v2",
        "scenario_identity": scenario_identity,
        "payload_hashes": payload_hashes,
        "bundle_identity": bundle_identity,
    }
    (root / "bundle_index.json").write_bytes(_canonical_file(index))
    return root, bundle_identity


def _observation(
    *,
    effective_date: str,
    bundle: object,
    available_date: str,
) -> FinancialCascadeObservation:
    return FinancialCascadeObservation(
        effective_date=effective_date,
        source_as_of_utc=f"{available_date}T00:00:00Z",
        available_at_utc=f"{available_date}T01:00:00Z",
        bundle=bundle,
    )


def test_bundle_adapter_verifies_exact_custody_and_ignores_bailout_ranking(
    tmp_path: Path,
) -> None:
    path_a, identity_a = _write_bundle(
        tmp_path / "a",
        scenario_id="cascade-a",
        shock_defaults=["A", "B", "C"],
        shock_unpaid=Fraction(217, 20),
        preferred="inject-A",
    )
    bundle_a = load_verified_leningrad_bundle(
        path_a, expected_bundle_identity=identity_a
    )
    assert bundle_a.shock_default_fraction == Fraction(1)
    assert bundle_a.shock_unpaid_fraction == Fraction(217, 440)
    assert bundle_a.preferred_intervention_id == "inject-A"
    assert classify_financial_cascade(bundle_a) is CascadeRiskState.SEVERE

    path_b, identity_b = _write_bundle(
        tmp_path / "b",
        scenario_id="cascade-b",
        shock_defaults=["A", "B", "C"],
        shock_unpaid=Fraction(217, 20),
        preferred="inject-B",
    )
    bundle_b = load_verified_leningrad_bundle(
        path_b, expected_bundle_identity=identity_b
    )
    assert bundle_b.preferred_intervention_id == "inject-B"
    assert classify_financial_cascade(bundle_b) is CascadeRiskState.SEVERE

    with pytest.raises(
        FinancialCascadeError, match="CASCADE_EXTERNAL_VERIFIER_IDENTITY_MISMATCH"
    ):
        load_verified_leningrad_bundle(path_b, expected_bundle_identity=identity_a)

    comparison_path = path_a / "comparison.json"
    comparison_path.write_bytes(comparison_path.read_bytes().replace(b'"inject-A"', b'"inject-B"', 1))
    with pytest.raises(
        FinancialCascadeError,
        match=(
            "CASCADE_COMPARISON_JSON_INVALID|"
            "CASCADE_COMPARISON_NOT_CANONICAL|"
            "CASCADE_PAYLOAD_HASH_MISMATCH"
        ),
    ):
        load_verified_leningrad_bundle(path_a, expected_bundle_identity=identity_a)


def test_bundle_adapter_accepts_leningrad_windows_crlf_without_weakening_hashes(
    tmp_path: Path,
) -> None:
    path, identity = _write_bundle(
        tmp_path / "crlf",
        scenario_id="crlf-bundle",
        shock_defaults=["A", "B"],
        shock_unpaid=4,
    )
    for name in ("bundle_index.json", "scenario.json", "comparison.json"):
        file_path = path / name
        file_path.write_bytes(file_path.read_bytes().replace(b"\n", b"\r\n"))

    payload_hashes = {
        name: sha256((path / name).read_bytes()).hexdigest()
        for name in ("scenario.json", "comparison.json", "report.md")
    }
    new_identity = _identity(
        {
            "kind": "finance-intervention-choice-bundle-identity-v2",
            "payload_hashes": payload_hashes,
        }
    )
    index = json.loads((path / "bundle_index.json").read_text(encoding="utf-8"))
    index["payload_hashes"] = payload_hashes
    index["bundle_identity"] = new_identity
    (path / "bundle_index.json").write_bytes(
        _canonical_file(index).replace(b"\n", b"\r\n")
    )

    loaded = load_verified_leningrad_bundle(
        path, expected_bundle_identity=new_identity
    )
    assert loaded.bundle_identity == new_identity
    assert loaded.bundle_identity != identity


def test_observation_requires_next_day_effective_date(tmp_path: Path) -> None:
    path, identity = _write_bundle(
        tmp_path / "pit",
        scenario_id="pit-bundle",
        shock_defaults=["A"],
        shock_unpaid=1,
    )
    bundle = load_verified_leningrad_bundle(path, expected_bundle_identity=identity)
    with pytest.raises(
        ValueError, match="CASCADE_EFFECTIVE_DATE_MUST_FOLLOW_AVAILABILITY_DATE"
    ):
        FinancialCascadeObservation(
            effective_date="2020-01-02",
            source_as_of_utc="2020-01-02T00:00:00Z",
            available_at_utc="2020-01-02T01:00:00Z",
            bundle=bundle,
        )


def test_overlay_caps_gross_only_and_preserves_selection_entry_exit_support(
    tmp_path: Path,
) -> None:
    severe_path, severe_identity = _write_bundle(
        tmp_path / "severe",
        scenario_id="severe",
        shock_defaults=["A", "B"],
        shock_unpaid=4,
    )
    clear_path, clear_identity = _write_bundle(
        tmp_path / "clear",
        scenario_id="clear",
        shock_defaults=[],
        shock_unpaid=0,
    )
    severe = load_verified_leningrad_bundle(
        severe_path, expected_bundle_identity=severe_identity
    )
    clear = load_verified_leningrad_bundle(
        clear_path, expected_bundle_identity=clear_identity
    )
    dates = pd.date_range("2020-01-01", periods=5, freq="D")
    observations = (
        _observation(
            effective_date="2020-01-02", bundle=severe, available_date="2020-01-01"
        ),
        _observation(
            effective_date="2020-01-05", bundle=clear, available_date="2020-01-04"
        ),
    )
    overlay = build_financial_cascade_overlay(observations, dates)
    assert overlay.loc[dates[0], "cascade_state"] == "UNAVAILABLE"
    assert overlay.loc[dates[1], "cascade_state"] == "SEVERE"
    assert overlay.loc[dates[4], "cascade_state"] == "CLEAR"

    weights = pd.DataFrame(
        {
            "LONG_A": [0.60] * 5,
            "LONG_B": [0.30] * 5,
            "SHORT_C": [-0.10] * 5,
        },
        index=dates,
    )
    capped = apply_financial_cascade_cap(weights, overlay)
    pd.testing.assert_series_equal(capped.target_weights.iloc[0], weights.iloc[0])
    assert capped.target_weights.iloc[1].abs().sum() == pytest.approx(0.50)
    assert capped.target_weights.iloc[4].abs().sum() == pytest.approx(1.00)
    assert tuple(capped.target_weights.columns) == tuple(weights.columns)
    assert (capped.target_weights.ne(0) == weights.ne(0)).all().all()
    assert (
        capped.target_weights.iloc[1] / weights.iloc[1]
    ).nunique() == 1
    assert capped.target_weights.iloc[1]["SHORT_C"] < 0


def test_same_engine_shadow_promotes_only_after_two_distinct_pit_windows(
    tmp_path: Path,
) -> None:
    first_path, first_identity = _write_bundle(
        tmp_path / "first",
        scenario_id="stress-one",
        shock_defaults=["A", "B"],
        shock_unpaid=4,
    )
    second_path, second_identity = _write_bundle(
        tmp_path / "second",
        scenario_id="stress-two",
        shock_defaults=["A", "B", "C"],
        shock_unpaid=8,
    )
    first = load_verified_leningrad_bundle(
        first_path, expected_bundle_identity=first_identity
    )
    second = load_verified_leningrad_bundle(
        second_path, expected_bundle_identity=second_identity
    )

    dates = pd.date_range("2020-03-01", periods=10, freq="D")
    weights = pd.DataFrame({"BANKS": [1.0] * 10}, index=dates)
    returns = pd.DataFrame(
        {"BANKS": [0.0, -0.04, -0.03, -0.02, -0.01, -0.05, -0.04, -0.03, -0.02, -0.01]},
        index=dates,
    )
    observations = (
        _observation(
            effective_date="2020-03-01", bundle=first, available_date="2020-02-29"
        ),
        _observation(
            effective_date="2020-03-06", bundle=second, available_date="2020-03-05"
        ),
    )
    windows = (
        StressWindow("W1", "2020-03-01", "2020-03-05"),
        StressWindow("W2", "2020-03-06", "2020-03-10"),
    )
    report = run_financial_cascade_shadow(
        target_weights=weights,
        returns_df=returns,
        observations=observations,
        stress_windows=windows,
        cost_rate=0.001,
    )
    assert report["decision"] == "PROMOTE_TO_LATER_PORTFOLIO_PREVIEW_CHALLENGER"
    assert report["gates"] == {
        "independent_windows": True,
        "pit_lineage": True,
        "all_window_drawdown_and_expected_shortfall": True,
        "annualized_net_alpha_drag": True,
        "bounded_turnover_increase": True,
        "exact_replay": True,
    }
    assert all(row["relative_max_drawdown_improvement"] >= 0.49 for row in report["window_results"])
    assert all(row["relative_expected_shortfall_improvement"] >= 0.49 for row in report["window_results"])
    assert report["security_selection_changed"] is False
    assert report["entry_exit_logic_changed"] is False
    assert report["intervention_ranking_used_for_trades"] is False

    weak_policy = FinancialCascadePolicy(
        severe_default_fraction=Fraction(1, 3),
        severe_unpaid_fraction=Fraction(1, 10),
        watch_gross_cap=0.95,
        severe_gross_cap=0.95,
    )
    killed = run_financial_cascade_shadow(
        target_weights=weights,
        returns_df=returns,
        observations=observations,
        stress_windows=windows,
        cost_rate=0.001,
        policy=weak_policy,
    )
    assert killed["decision"] == "KILL_CHALLENGER"

    deferred = run_financial_cascade_shadow(
        target_weights=weights,
        returns_df=returns,
        observations=observations[:1],
        stress_windows=windows[:1],
        cost_rate=0.001,
        thresholds=CascadePromotionThresholds(min_window_observations=5),
    )
    assert deferred["decision"] == "DEFER_INSUFFICIENT_EVIDENCE"

    with pytest.raises(ValueError, match="CASCADE_WINDOW_OUTSIDE_BACKTEST"):
        run_financial_cascade_shadow(
            target_weights=weights,
            returns_df=returns,
            observations=observations[:1],
            stress_windows=(
                StressWindow("BAD", "2020-02-28", "2020-03-02"),
            ),
            cost_rate=0.001,
        )


def test_cli_runs_atomic_same_engine_report(tmp_path: Path) -> None:
    first_path, first_identity = _write_bundle(
        tmp_path / "first-cli",
        scenario_id="cli-stress-one",
        shock_defaults=["A", "B"],
        shock_unpaid=4,
    )
    second_path, second_identity = _write_bundle(
        tmp_path / "second-cli",
        scenario_id="cli-stress-two",
        shock_defaults=["A", "B", "C"],
        shock_unpaid=8,
    )
    dates = pd.date_range("2020-04-01", periods=10, freq="D")
    weights_path = tmp_path / "weights.csv"
    returns_path = tmp_path / "returns.csv"
    pd.DataFrame({"BANKS": [1.0] * 10}, index=dates).to_csv(weights_path)
    pd.DataFrame(
        {"BANKS": [0.0, -0.04, -0.03, -0.02, -0.01, -0.05, -0.04, -0.03, -0.02, -0.01]},
        index=dates,
    ).to_csv(returns_path)
    manifest_path = tmp_path / "observations.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "quant-financial-cascade-observations-v1",
                "observations": [
                    {
                        "effective_date": "2020-04-01",
                        "source_as_of_utc": "2020-03-31T00:00:00Z",
                        "available_at_utc": "2020-03-31T01:00:00Z",
                        "bundle_path": str(first_path),
                        "expected_bundle_identity": first_identity,
                    },
                    {
                        "effective_date": "2020-04-06",
                        "source_as_of_utc": "2020-04-05T00:00:00Z",
                        "available_at_utc": "2020-04-05T01:00:00Z",
                        "bundle_path": str(second_path),
                        "expected_bundle_identity": second_identity,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "report.json"
    assert (
        cascade_cli_main(
            [
                "--weights-csv",
                str(weights_path),
                "--returns-csv",
                str(returns_path),
                "--observations-json",
                str(manifest_path),
                "--stress-window",
                "W1:2020-04-01:2020-04-05",
                "--stress-window",
                "W2:2020-04-06:2020-04-10",
                "--output-json",
                str(output_path),
            ]
        )
        == 0
    )
    stored = json.loads(output_path.read_text(encoding="utf-8"))
    assert stored["decision"] == "PROMOTE_TO_LATER_PORTFOLIO_PREVIEW_CHALLENGER"
    assert len(stored["execution_identity"]) == 64
    assert stored["inputs"]["weights_csv_sha256"] == sha256(
        weights_path.read_bytes()
    ).hexdigest()
    assert not list(tmp_path.glob(".report.json.*.tmp"))
