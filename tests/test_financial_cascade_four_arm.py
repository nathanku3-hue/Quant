from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import pandas as pd
import pytest

from research.financial_cascade_four_arm import (
    ENGINEERING_ONLY,
    GOVERNED_PIT,
    RESTORE_FROZEN_BASELINE_TARGET,
    CascadeExperimentExitRule,
    FinancialCascadeFourArmError,
    GovernedCascadeEvidence,
    load_existing_g5_nonzero_portfolio,
    run_financial_cascade_four_arm,
)
from scripts import run_financial_cascade_four_arm as four_arm_cli
from strategies.financial_cascade import (
    FinancialCascadeBundle,
    FinancialCascadeObservation,
)


def _severe_bundle() -> FinancialCascadeBundle:
    return FinancialCascadeBundle(
        scenario_id="engineering-cascade",
        scenario_identity="1" * 64,
        bundle_identity="2" * 64,
        institution_ids=("A", "B", "C"),
        nominal_obligations=Fraction(22),
        shock_default_count=3,
        shock_unpaid_obligations=Fraction(10),
        shock_default_fraction=Fraction(1),
        shock_unpaid_fraction=Fraction(5, 11),
        non_unique_states=(),
        decision="candidate_preferred",
        preferred_intervention_id="inject-A",
    )


def _observation() -> FinancialCascadeObservation:
    return FinancialCascadeObservation(
        effective_date="2024-01-16",
        source_as_of_utc="2024-01-15T00:00:00Z",
        available_at_utc="2024-01-15T01:00:00Z",
        bundle=_severe_bundle(),
    )


def _exit_rule() -> CascadeExperimentExitRule:
    return CascadeExperimentExitRule(
        overlay_effective_date="2024-01-16",
        evaluation_horizon_end_date="2024-02-29",
        maximum_holding_period_sessions=10,
        manual_review_date="2024-01-29",
        terminal_disposition=RESTORE_FROZEN_BASELINE_TARGET,
        reconciliation_date="2024-02-29",
    )


def _macro(index: pd.DatetimeIndex) -> pd.DataFrame:
    # This is consumed by the existing RegimeManager legacy-scalar fallback.
    return pd.DataFrame({"regime_scalar": 0.75}, index=index)


def test_existing_g5_portfolio_is_real_nonzero_and_identity_bound() -> None:
    portfolio = load_existing_g5_nonzero_portfolio()

    assert portfolio.target_weights.shape == (41, 3)
    assert portfolio.returns_df.shape == (41, 3)
    assert (portfolio.target_weights.abs().sum(axis=1) == 1.0).all()
    assert portfolio.source_identity["portfolio_id"] == (
        "PH65_G5_PREDECLARED_NEUTRAL_PORTFOLIO"
    )
    assert portfolio.source_identity["dataset_name"] == (
        "prices_tri_real_canonical_tiny_slice"
    )
    assert len(portfolio.source_identity["artifact_sha256"]) == 64
    assert len(portfolio.source_identity["target_weight_digest"]) == 64


def test_four_arm_uses_min_cap_not_sequential_scalar_multiplication() -> None:
    portfolio = load_existing_g5_nonzero_portfolio()
    report = run_financial_cascade_four_arm(
        target_weights=portfolio.target_weights,
        returns_df=portfolio.returns_df,
        macro_df=_macro(pd.DatetimeIndex(portfolio.target_weights.index)),
        observations=(_observation(),),
        exit_rule=_exit_rule(),
        portfolio_source_identity=portfolio.source_identity,
        evidence_classification=ENGINEERING_ONLY,
    )

    assert report["evidence_classification"] == ENGINEERING_ONLY
    assert report["decision"] == "ENGINEERING_COMPLETE_NO_ALPHA_AUTHORITY"
    assert report["capital_authority"] is False
    assert report["score_uplift_authorized"] is False
    assert report["alpha_claim_authorized"] is False
    assert report["sequential_scalar_multiplication_used"] is False
    assert report["combined_cap_formula"].startswith("min(")
    assert set(report["arms"]) == {
        "A_UNCAPPED_BASELINE",
        "B_EXISTING_REGIME_ONLY",
        "C_CASCADE_ONLY",
        "D_REGIME_AND_CASCADE",
    }

    # Regime permits 0.75 and cascade permits 0.50. Frozen D is 0.50,
    # never the sequential product 0.375.
    assert report["arms"]["B_EXISTING_REGIME_ONLY"][
        "minimum_target_gross"
    ] == pytest.approx(0.75)
    assert report["arms"]["D_REGIME_AND_CASCADE"][
        "minimum_target_gross"
    ] == pytest.approx(0.50)
    assert report["arms"]["D_REGIME_AND_CASCADE"][
        "minimum_target_gross"
    ] != pytest.approx(0.375)
    assert report["replay"]["exact_replay"] is True


def test_incremental_vector_receipt_and_exit_rule_are_complete() -> None:
    portfolio = load_existing_g5_nonzero_portfolio()
    report = run_financial_cascade_four_arm(
        target_weights=portfolio.target_weights,
        returns_df=portfolio.returns_df,
        macro_df=_macro(pd.DatetimeIndex(portfolio.target_weights.index)),
        observations=(_observation(),),
        exit_rule=_exit_rule(),
        portfolio_source_identity=portfolio.source_identity,
    )

    incremental = report["incremental_d_vs_b"]
    assert set(incremental) == {
        "comparison",
        "delta_compounded_net_return",
        "delta_maximum_drawdown_abs",
        "delta_expected_shortfall",
        "delta_total_turnover",
        "missed_upside",
        "avoided_loss",
        "reduced_exposure_days",
        "reentry_status",
        "reentry_delay_sessions",
        "reentry_date",
    }
    assert incremental["comparison"] == (
        "D_REGIME_AND_CASCADE_MINUS_B_EXISTING_REGIME_ONLY"
    )
    assert incremental["reduced_exposure_days"] > 0
    assert incremental["reentry_status"] == "REENTERED_TO_REGIME_PATH"
    assert incremental["reentry_delay_sessions"] == 0
    assert incremental["reentry_date"] == "2024-01-29"

    receipts = report["prospective_receipts"]
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["evidence_classification"] == ENGINEERING_ONLY
    assert receipt["capital_authority"] is False
    assert receipt["score_uplift_authorized"] is False
    assert receipt["alpha_claim_authorized"] is False
    assert receipt["regime_permitted_gross"] == pytest.approx(0.75)
    assert receipt["cascade_permitted_gross"] == pytest.approx(0.50)
    assert receipt["combined_permitted_gross"] == pytest.approx(0.50)
    assert receipt["incremental_information"] == "TIGHTER_THAN_EXISTING_REGIME"
    assert receipt["exit_rule"]["manual_review_date"] == "2024-01-29"
    assert receipt["exit_rule"]["terminal_disposition"] == (
        RESTORE_FROZEN_BASELINE_TARGET
    )
    assert len(receipt["receipt_identity"]) == 64


def test_governed_pit_classification_requires_exact_source_proof() -> None:
    portfolio = load_existing_g5_nonzero_portfolio()
    kwargs = {
        "target_weights": portfolio.target_weights,
        "returns_df": portfolio.returns_df,
        "macro_df": _macro(pd.DatetimeIndex(portfolio.target_weights.index)),
        "observations": (_observation(),),
        "exit_rule": _exit_rule(),
        "portfolio_source_identity": portfolio.source_identity,
        "evidence_classification": GOVERNED_PIT,
    }
    with pytest.raises(
        FinancialCascadeFourArmError, match="CASCADE_GOVERNED_PIT_PROOF_REQUIRED"
    ):
        run_financial_cascade_four_arm(**kwargs)

    proof = GovernedCascadeEvidence(
        institutional_network_source_identity="authority://network/1",
        liabilities_source_identity="authority://liabilities/1",
        shock_source_identity="authority://shock/1",
        source_as_of_utc="2024-01-15T00:00:00Z",
        available_at_utc="2024-01-15T01:00:00Z",
    )
    report = run_financial_cascade_four_arm(
        **kwargs,
        governed_evidence_by_bundle={_severe_bundle().bundle_identity: proof},
    )
    assert report["evidence_classification"] == GOVERNED_PIT
    assert report["decision"] == (
        "GOVERNED_PIT_EVIDENCE_READY_FOR_PAPER_BRIDGE_REVIEW"
    )
    assert report["capital_authority"] is False


def test_cli_writes_atomic_engineering_only_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    for name in ("scenario.json", "comparison.json", "report.md", "bundle_index.json"):
        (bundle_dir / name).write_text(f"fixture:{name}\n", encoding="utf-8")
    monkeypatch.setattr(
        four_arm_cli,
        "load_verified_leningrad_bundle",
        lambda *_args, **_kwargs: _severe_bundle(),
    )
    output = tmp_path / "four-arm.json"

    result = four_arm_cli.main(
        [
            "--bundle-dir",
            str(bundle_dir),
            "--bundle-identity",
            _severe_bundle().bundle_identity,
            "--source-as-of-utc",
            "2024-01-15T00:00:00Z",
            "--available-at-utc",
            "2024-01-15T01:00:00Z",
            "--effective-date",
            "2024-01-16",
            "--regime-step",
            "2024-01-02:0.75",
            "--evaluation-horizon-end",
            "2024-02-29",
            "--maximum-holding-sessions",
            "10",
            "--manual-review-date",
            "2024-01-29",
            "--terminal-disposition",
            RESTORE_FROZEN_BASELINE_TARGET,
            "--reconciliation-date",
            "2024-02-29",
            "--output-json",
            str(output),
        ]
    )

    assert result == 0
    stored = json.loads(output.read_text(encoding="utf-8"))
    assert stored["evidence_classification"] == ENGINEERING_ONLY
    assert stored["capital_authority"] is False
    assert len(stored["execution_identity"]) == 64
    assert stored["cli_inputs"]["governed_proof_sha256"] is None
    assert not list(tmp_path.glob(".four-arm.json.*.tmp"))
