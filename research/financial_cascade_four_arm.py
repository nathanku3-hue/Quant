"""Four-arm attribution experiment for the Leningrad cascade challenger.

The module measures whether cascade evidence adds anything beyond Quant's
existing RegimeManager. It owns no capital authority. A synthetic or otherwise
ungoverned cascade observation is always ENGINEERING_ONLY.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from core.engine import run_simulation
from data.provenance import compute_sha256
from research.financial_cascade_shadow import expected_shortfall
from research.metrics import build_equity_curve, max_drawdown
from strategies.financial_cascade import (
    FinancialCascadeObservation,
    FinancialCascadePolicy,
    build_financial_cascade_overlay,
)
from strategies.regime_manager import RegimeManager
from v2_discovery.readiness.canonical_slice import load_g4_canonical_slice
from v2_discovery.replay.canonical_real_replay import (
    build_predeclared_neutral_weights,
)


ENGINEERING_ONLY = "ENGINEERING_ONLY"
GOVERNED_PIT = "GOVERNED_PIT"
RESTORE_FROZEN_BASELINE_TARGET = "RESTORE_FROZEN_BASELINE_TARGET"
REMAIN_REDUCED = "REMAIN_REDUCED"


class FinancialCascadeFourArmError(ValueError):
    """Fail-closed four-arm experiment error."""


@dataclass(frozen=True, slots=True)
class CascadeExperimentExitRule:
    overlay_effective_date: str
    evaluation_horizon_end_date: str
    maximum_holding_period_sessions: int
    manual_review_date: str
    terminal_disposition: str
    reconciliation_date: str

    def __post_init__(self) -> None:
        dates = {
            "overlay_effective_date": self.overlay_effective_date,
            "evaluation_horizon_end_date": self.evaluation_horizon_end_date,
            "manual_review_date": self.manual_review_date,
            "reconciliation_date": self.reconciliation_date,
        }
        parsed: dict[str, pd.Timestamp] = {}
        for field, value in dates.items():
            try:
                timestamp = pd.Timestamp(value)
            except (TypeError, ValueError) as exc:
                raise FinancialCascadeFourArmError(
                    f"CASCADE_EXPERIMENT_{field.upper()}_INVALID"
                ) from exc
            if timestamp.tzinfo is not None or timestamp != timestamp.normalize():
                raise FinancialCascadeFourArmError(
                    f"CASCADE_EXPERIMENT_{field.upper()}_MUST_BE_NAIVE_DATE"
                )
            if value != timestamp.date().isoformat():
                raise FinancialCascadeFourArmError(
                    f"CASCADE_EXPERIMENT_{field.upper()}_NOT_CANONICAL"
                )
            parsed[field] = timestamp
        if isinstance(self.maximum_holding_period_sessions, bool) or not isinstance(
            self.maximum_holding_period_sessions, int
        ):
            raise TypeError("CASCADE_EXPERIMENT_MAX_HOLDING_SESSIONS_TYPE_INVALID")
        if self.maximum_holding_period_sessions <= 0:
            raise FinancialCascadeFourArmError(
                "CASCADE_EXPERIMENT_MAX_HOLDING_SESSIONS_POSITIVE_REQUIRED"
            )
        if parsed["manual_review_date"] < parsed["overlay_effective_date"]:
            raise FinancialCascadeFourArmError(
                "CASCADE_EXPERIMENT_REVIEW_BEFORE_EFFECTIVE"
            )
        if parsed["evaluation_horizon_end_date"] < parsed["manual_review_date"]:
            raise FinancialCascadeFourArmError(
                "CASCADE_EXPERIMENT_HORIZON_BEFORE_REVIEW"
            )
        if parsed["reconciliation_date"] < parsed["evaluation_horizon_end_date"]:
            raise FinancialCascadeFourArmError(
                "CASCADE_EXPERIMENT_RECONCILIATION_BEFORE_HORIZON"
            )
        if self.terminal_disposition not in {
            RESTORE_FROZEN_BASELINE_TARGET,
            REMAIN_REDUCED,
        }:
            raise FinancialCascadeFourArmError(
                "CASCADE_EXPERIMENT_TERMINAL_DISPOSITION_INVALID"
            )


@dataclass(frozen=True, slots=True)
class GovernedCascadeEvidence:
    institutional_network_source_identity: str
    liabilities_source_identity: str
    shock_source_identity: str
    source_as_of_utc: str
    available_at_utc: str

    def __post_init__(self) -> None:
        for field in (
            "institutional_network_source_identity",
            "liabilities_source_identity",
            "shock_source_identity",
            "source_as_of_utc",
            "available_at_utc",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise FinancialCascadeFourArmError(
                    f"CASCADE_GOVERNED_{field.upper()}_REQUIRED"
                )
        source = pd.Timestamp(self.source_as_of_utc)
        available = pd.Timestamp(self.available_at_utc)
        if source.tzinfo is None or available.tzinfo is None:
            raise FinancialCascadeFourArmError(
                "CASCADE_GOVERNED_TIMESTAMPS_MUST_BE_TZ_AWARE"
            )
        if available.tz_convert("UTC") < source.tz_convert("UTC"):
            raise FinancialCascadeFourArmError(
                "CASCADE_GOVERNED_AVAILABLE_BEFORE_SOURCE"
            )


@dataclass(frozen=True, slots=True)
class ExistingPortfolioInputs:
    target_weights: pd.DataFrame
    returns_df: pd.DataFrame
    source_identity: dict[str, Any]


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def _frame_digest(frame: pd.DataFrame) -> str:
    value = {
        "index": [pd.Timestamp(item).isoformat() for item in frame.index],
        "columns": [str(column) for column in frame.columns],
        "data": [
            [format(float(item), ".17g") for item in row]
            for row in frame.to_numpy(dtype=float)
        ],
    }
    return _canonical_digest(value)


def _row_digest(row: pd.Series) -> str:
    return _canonical_digest(
        {
            "columns": [str(column) for column in row.index],
            "values": [format(float(value), ".17g") for value in row.to_numpy()],
        }
    )


def load_existing_g5_nonzero_portfolio(
    *, repo_root: str | Path | None = None
) -> ExistingPortfolioInputs:
    """Load the existing G5 canonical equal-weight nonzero portfolio."""

    root = Path(repo_root) if repo_root is not None else Path.cwd()
    canonical_slice = load_g4_canonical_slice(repo_root=root)
    data = canonical_slice.data.copy()
    weights = build_predeclared_neutral_weights(data)
    framed = data.assign(_date=pd.to_datetime(data["date"], errors="coerce"))
    returns_df = framed.pivot(
        index="_date", columns="permno", values="total_ret"
    ).sort_index()
    returns_df = returns_df.reindex(index=weights.index, columns=weights.columns)
    if returns_df.isna().any().any():
        raise FinancialCascadeFourArmError(
            "CASCADE_G5_RETURN_MATRIX_INCOMPLETE"
        )
    source_identity = {
        "portfolio_id": "PH65_G5_PREDECLARED_NEUTRAL_PORTFOLIO",
        "dataset_name": canonical_slice.dataset_name,
        "artifact_uri": canonical_slice.artifact_uri,
        "artifact_sha256": compute_sha256(canonical_slice.artifact_path),
        "manifest_uri": canonical_slice.manifest_uri,
        "manifest_sha256": compute_sha256(canonical_slice.manifest_path),
        "weight_rule": "G5_PREDECLARED_EQUAL_WEIGHT",
        "target_weight_digest": _frame_digest(weights),
        "returns_digest": _frame_digest(returns_df),
    }
    return ExistingPortfolioInputs(
        target_weights=weights.astype(float),
        returns_df=returns_df.astype(float),
        source_identity=source_identity,
    )


def _validate_inputs(
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    macro_df: pd.DataFrame,
) -> None:
    if not isinstance(target_weights, pd.DataFrame) or target_weights.empty:
        raise FinancialCascadeFourArmError("CASCADE_FOUR_ARM_WEIGHTS_REQUIRED")
    if not isinstance(returns_df, pd.DataFrame) or returns_df.empty:
        raise FinancialCascadeFourArmError("CASCADE_FOUR_ARM_RETURNS_REQUIRED")
    if not isinstance(macro_df, pd.DataFrame):
        raise TypeError("CASCADE_FOUR_ARM_MACRO_DATAFRAME_REQUIRED")
    if not target_weights.index.equals(returns_df.index):
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_WEIGHT_RETURN_INDEX_MISMATCH"
        )
    if not target_weights.columns.equals(returns_df.columns):
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_WEIGHT_RETURN_COLUMN_MISMATCH"
        )
    dates = pd.DatetimeIndex(target_weights.index)
    if (
        dates.tz is not None
        or dates.hasnans
        or dates.has_duplicates
        or not dates.is_monotonic_increasing
    ):
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_INDEX_MUST_BE_SORTED_UNIQUE_NAIVE_DATES"
        )
    for frame, code in (
        (target_weights, "CASCADE_FOUR_ARM_WEIGHTS_NON_FINITE"),
        (returns_df, "CASCADE_FOUR_ARM_RETURNS_NON_FINITE"),
    ):
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or not np.isfinite(
            numeric.to_numpy(dtype=float)
        ).all():
            raise FinancialCascadeFourArmError(code)
    if (target_weights.abs().sum(axis=1) <= 0.0).all():
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_NONZERO_PORTFOLIO_REQUIRED"
        )


def _validate_exit_rule_on_index(
    rule: CascadeExperimentExitRule, index: pd.DatetimeIndex
) -> None:
    effective = pd.Timestamp(rule.overlay_effective_date)
    review = pd.Timestamp(rule.manual_review_date)
    horizon = pd.Timestamp(rule.evaluation_horizon_end_date)
    for field, value in (
        ("EFFECTIVE", effective),
        ("MANUAL_REVIEW", review),
        ("HORIZON", horizon),
    ):
        if value not in index:
            raise FinancialCascadeFourArmError(
                f"CASCADE_EXPERIMENT_{field}_DATE_NOT_IN_PORTFOLIO_CALENDAR"
            )
    effective_position = int(index.get_loc(effective))
    review_position = int(index.get_loc(review))
    holding_sessions = review_position - effective_position
    if holding_sessions > rule.maximum_holding_period_sessions:
        raise FinancialCascadeFourArmError(
            "CASCADE_EXPERIMENT_REVIEW_EXCEEDS_MAX_HOLDING_PERIOD"
        )


def build_regime_controls(
    macro_df: pd.DataFrame, index: pd.DatetimeIndex
) -> pd.DataFrame:
    """Run the existing RegimeManager and expose its permitted gross."""

    result = RegimeManager().evaluate(macro_df, index)
    controls = pd.DataFrame(
        {
            "regime_state": result.governor_state,
            "market_state": result.market_state,
            "regime_permitted_gross": result.target_exposure,
            "regime_reason": result.reason,
        },
        index=index,
    )
    permitted = pd.to_numeric(
        controls["regime_permitted_gross"], errors="coerce"
    )
    if permitted.isna().any() or not np.isfinite(permitted.to_numpy()).all():
        raise FinancialCascadeFourArmError(
            "CASCADE_REGIME_PERMITTED_GROSS_NON_FINITE"
        )
    if (permitted < 0.0).any():
        raise FinancialCascadeFourArmError(
            "CASCADE_REGIME_PERMITTED_GROSS_NEGATIVE"
        )
    return controls


def _apply_gross_cap(
    target_weights: pd.DataFrame, permitted_gross: pd.Series
) -> pd.DataFrame:
    cap = pd.to_numeric(permitted_gross, errors="coerce").reindex(
        target_weights.index
    )
    if cap.isna().any() or not np.isfinite(cap.to_numpy()).all():
        raise FinancialCascadeFourArmError("CASCADE_GROSS_CAP_NON_FINITE")
    if (cap < 0.0).any():
        raise FinancialCascadeFourArmError("CASCADE_GROSS_CAP_NEGATIVE")
    gross = target_weights.abs().sum(axis=1)
    scale = pd.Series(1.0, index=target_weights.index, dtype=float)
    constrained = (gross > 0.0) & (gross > cap)
    scale.loc[constrained] = cap.loc[constrained] / gross.loc[constrained]
    return target_weights.astype(float).mul(scale, axis=0)


def _bound_cascade_cap(
    overlay: pd.DataFrame,
    index: pd.DatetimeIndex,
    rule: CascadeExperimentExitRule,
    uncapped_gross: pd.Series,
) -> pd.Series:
    cap = pd.to_numeric(overlay["gross_exposure_cap"], errors="coerce").reindex(
        index
    )
    # No cascade cap means the portfolio's own gross ceiling.
    bounded = cap.where(cap.notna(), uncapped_gross).astype(float)
    effective = pd.Timestamp(rule.overlay_effective_date)
    review = pd.Timestamp(rule.manual_review_date)
    bounded.loc[index < effective] = uncapped_gross.loc[index < effective]
    if rule.terminal_disposition == RESTORE_FROZEN_BASELINE_TARGET:
        bounded.loc[index >= review] = uncapped_gross.loc[index >= review]
    return bounded


def _verify_governed_evidence(
    observations: tuple[FinancialCascadeObservation, ...],
    evidence_classification: str,
    governed_evidence_by_bundle: Mapping[str, GovernedCascadeEvidence] | None,
) -> None:
    if evidence_classification not in {ENGINEERING_ONLY, GOVERNED_PIT}:
        raise FinancialCascadeFourArmError(
            "CASCADE_EVIDENCE_CLASSIFICATION_INVALID"
        )
    if evidence_classification == ENGINEERING_ONLY:
        return
    if not governed_evidence_by_bundle:
        raise FinancialCascadeFourArmError(
            "CASCADE_GOVERNED_PIT_PROOF_REQUIRED"
        )
    for observation in observations:
        proof = governed_evidence_by_bundle.get(observation.bundle.bundle_identity)
        if not isinstance(proof, GovernedCascadeEvidence):
            raise FinancialCascadeFourArmError(
                "CASCADE_GOVERNED_PIT_BUNDLE_PROOF_REQUIRED"
            )
        if proof.source_as_of_utc != observation.source_as_of_utc:
            raise FinancialCascadeFourArmError(
                "CASCADE_GOVERNED_SOURCE_AS_OF_MISMATCH"
            )
        if proof.available_at_utc != observation.available_at_utc:
            raise FinancialCascadeFourArmError(
                "CASCADE_GOVERNED_AVAILABLE_AT_MISMATCH"
            )


def _arm_metrics(
    simulation: pd.DataFrame,
    weights: pd.DataFrame,
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    net = pd.to_numeric(simulation["net_ret"], errors="raise").astype(float)
    gross = weights.abs().sum(axis=1).astype(float)
    return {
        "compounded_net_return": float((1.0 + net).prod() - 1.0),
        "maximum_drawdown_abs": float(
            abs(max_drawdown(build_equity_curve(net)))
        ),
        "expected_shortfall": float(
            expected_shortfall(net, confidence=confidence)
        ),
        "total_turnover": float(
            pd.to_numeric(simulation["turnover"], errors="raise").sum()
        ),
        "total_cost": float(
            pd.to_numeric(simulation["cost"], errors="raise").sum()
        ),
        "average_target_gross": float(gross.mean()),
        "minimum_target_gross": float(gross.min()),
        "maximum_target_gross": float(gross.max()),
        "target_weight_digest": _frame_digest(weights),
        "simulation_digest": _frame_digest(simulation),
    }


def _reentry_result(
    *,
    regime_only_weights: pd.DataFrame,
    combined_weights: pd.DataFrame,
    rule: CascadeExperimentExitRule,
) -> dict[str, Any]:
    index = pd.DatetimeIndex(regime_only_weights.index)
    review = pd.Timestamp(rule.manual_review_date)
    start_position = int(index.get_loc(review))
    regime_gross = regime_only_weights.abs().sum(axis=1)
    combined_gross = combined_weights.abs().sum(axis=1)
    matches = np.isclose(
        combined_gross.iloc[start_position:].to_numpy(dtype=float),
        regime_gross.iloc[start_position:].to_numpy(dtype=float),
        atol=1e-12,
        rtol=0.0,
    )
    positions = np.flatnonzero(matches)
    if positions.size:
        return {
            "reentry_status": "REENTERED_TO_REGIME_PATH",
            "reentry_delay_sessions": int(positions[0]),
            "reentry_date": index[start_position + int(positions[0])]
            .date()
            .isoformat(),
        }
    return {
        "reentry_status": "NOT_REENTERED_WITHIN_EVALUATION_HORIZON",
        "reentry_delay_sessions": None,
        "reentry_date": None,
    }


def _build_receipts(
    *,
    observations: tuple[FinancialCascadeObservation, ...],
    target_weights: pd.DataFrame,
    regime_controls: pd.DataFrame,
    cascade_overlay: pd.DataFrame,
    combined_cap: pd.Series,
    evidence_classification: str,
    exit_rule: CascadeExperimentExitRule,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    gross = target_weights.abs().sum(axis=1)
    for observation in observations:
        effective = pd.Timestamp(observation.effective_date)
        if effective not in target_weights.index:
            continue
        cascade_cap_raw = cascade_overlay.loc[effective, "gross_exposure_cap"]
        cascade_cap = (
            None if pd.isna(cascade_cap_raw) else float(cascade_cap_raw)
        )
        regime_cap = float(
            regime_controls.loc[effective, "regime_permitted_gross"]
        )
        uncapped = float(gross.loc[effective])
        combined = float(combined_cap.loc[effective])
        if cascade_cap is None or cascade_cap >= min(uncapped, regime_cap):
            incremental_information = "REDUNDANT_OR_LOOSER_THAN_EXISTING_REGIME"
        else:
            incremental_information = "TIGHTER_THAN_EXISTING_REGIME"
        body = {
            "schema_version": "quant-financial-cascade-prospective-receipt-v1",
            "evidence_classification": evidence_classification,
            "capital_authority": False,
            "score_uplift_authorized": False,
            "alpha_claim_authorized": False,
            "bundle_identity": observation.bundle.bundle_identity,
            "scenario_identity": observation.bundle.scenario_identity,
            "source_as_of_utc": observation.source_as_of_utc,
            "available_at_utc": observation.available_at_utc,
            "effective_date": observation.effective_date,
            "target_weight_row_digest": _row_digest(
                target_weights.loc[effective]
            ),
            "uncapped_portfolio_gross": uncapped,
            "regime_state": str(
                regime_controls.loc[effective, "regime_state"]
            ),
            "regime_reason": str(
                regime_controls.loc[effective, "regime_reason"]
            ),
            "regime_permitted_gross": regime_cap,
            "cascade_state": str(
                cascade_overlay.loc[effective, "cascade_state"]
            ),
            "cascade_permitted_gross": cascade_cap,
            "combined_permitted_gross": combined,
            "combined_cap_formula": (
                "min(uncapped_portfolio_gross, regime_permitted_gross, "
                "cascade_permitted_gross)"
            ),
            "incremental_information": incremental_information,
            "exit_rule": {
                "overlay_effective_date": exit_rule.overlay_effective_date,
                "evaluation_horizon_end_date": (
                    exit_rule.evaluation_horizon_end_date
                ),
                "maximum_holding_period_sessions": (
                    exit_rule.maximum_holding_period_sessions
                ),
                "manual_review_date": exit_rule.manual_review_date,
                "terminal_disposition": exit_rule.terminal_disposition,
                "reconciliation_date": exit_rule.reconciliation_date,
            },
        }
        receipts.append(
            {
                **body,
                "receipt_identity": _canonical_digest(body),
            }
        )
    if not receipts:
        raise FinancialCascadeFourArmError(
            "CASCADE_PROSPECTIVE_RECEIPT_EFFECTIVE_DATE_NOT_IN_PORTFOLIO"
        )
    return receipts


def run_financial_cascade_four_arm(
    *,
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    macro_df: pd.DataFrame,
    observations: Iterable[FinancialCascadeObservation],
    exit_rule: CascadeExperimentExitRule,
    portfolio_source_identity: Mapping[str, Any],
    evidence_classification: str = ENGINEERING_ONLY,
    governed_evidence_by_bundle: Mapping[
        str, GovernedCascadeEvidence
    ] | None = None,
    cost_rate: float = 0.0010,
    policy: FinancialCascadePolicy | None = None,
) -> dict[str, Any]:
    """Run A/B/C/D through one engine and emit ex-ante receipts."""

    _validate_inputs(target_weights, returns_df, macro_df)
    observations_tuple = tuple(observations)
    if not observations_tuple:
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_OBSERVATION_REQUIRED"
        )
    if not isinstance(portfolio_source_identity, Mapping) or not dict(
        portfolio_source_identity
    ):
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_PORTFOLIO_SOURCE_IDENTITY_REQUIRED"
        )
    if not np.isfinite(cost_rate) or cost_rate < 0.0:
        raise FinancialCascadeFourArmError(
            "CASCADE_FOUR_ARM_COST_RATE_INVALID"
        )
    _verify_governed_evidence(
        observations_tuple,
        evidence_classification,
        governed_evidence_by_bundle,
    )

    full_index = pd.DatetimeIndex(target_weights.index)
    _validate_exit_rule_on_index(exit_rule, full_index)
    horizon = pd.Timestamp(exit_rule.evaluation_horizon_end_date)
    mask = full_index <= horizon
    weights = target_weights.loc[mask].astype(float)
    returns = returns_df.loc[mask].astype(float)
    macro = macro_df.reindex(weights.index)
    index = pd.DatetimeIndex(weights.index)

    regime_controls = build_regime_controls(macro, index)
    cascade_overlay = build_financial_cascade_overlay(
        observations_tuple,
        index,
        policy=policy or FinancialCascadePolicy(),
    )
    uncapped_gross = weights.abs().sum(axis=1).astype(float)
    regime_cap = pd.to_numeric(
        regime_controls["regime_permitted_gross"], errors="raise"
    ).astype(float)
    cascade_cap = _bound_cascade_cap(
        cascade_overlay,
        index,
        exit_rule,
        uncapped_gross,
    )
    # Frozen order-independent law. Never multiply regime and cascade scalars.
    combined_cap = pd.concat(
        [uncapped_gross, regime_cap, cascade_cap], axis=1
    ).min(axis=1)

    arm_weights = {
        "A_UNCAPPED_BASELINE": weights,
        "B_EXISTING_REGIME_ONLY": _apply_gross_cap(weights, regime_cap),
        "C_CASCADE_ONLY": _apply_gross_cap(weights, cascade_cap),
        "D_REGIME_AND_CASCADE": _apply_gross_cap(weights, combined_cap),
    }
    simulations = {
        name: run_simulation(
            target_weights=value,
            returns_df=returns,
            cost_bps=float(cost_rate),
            strict_missing_returns=True,
        )
        for name, value in arm_weights.items()
    }
    replay = run_simulation(
        target_weights=arm_weights["D_REGIME_AND_CASCADE"].copy(),
        returns_df=returns.copy(),
        cost_bps=float(cost_rate),
        strict_missing_returns=True,
    )
    exact_replay = bool(
        simulations["D_REGIME_AND_CASCADE"].equals(replay)
        and _frame_digest(simulations["D_REGIME_AND_CASCADE"])
        == _frame_digest(replay)
    )

    metrics = {
        name: _arm_metrics(simulations[name], arm_weights[name])
        for name in arm_weights
    }
    b_sim = simulations["B_EXISTING_REGIME_ONLY"]
    d_sim = simulations["D_REGIME_AND_CASCADE"]
    daily_increment = pd.to_numeric(d_sim["net_ret"]) - pd.to_numeric(
        b_sim["net_ret"]
    )
    b_gross = arm_weights["B_EXISTING_REGIME_ONLY"].abs().sum(axis=1)
    d_gross = arm_weights["D_REGIME_AND_CASCADE"].abs().sum(axis=1)
    reentry = _reentry_result(
        regime_only_weights=arm_weights["B_EXISTING_REGIME_ONLY"],
        combined_weights=arm_weights["D_REGIME_AND_CASCADE"],
        rule=exit_rule,
    )
    incremental = {
        "comparison": "D_REGIME_AND_CASCADE_MINUS_B_EXISTING_REGIME_ONLY",
        "delta_compounded_net_return": (
            metrics["D_REGIME_AND_CASCADE"]["compounded_net_return"]
            - metrics["B_EXISTING_REGIME_ONLY"]["compounded_net_return"]
        ),
        "delta_maximum_drawdown_abs": (
            metrics["D_REGIME_AND_CASCADE"]["maximum_drawdown_abs"]
            - metrics["B_EXISTING_REGIME_ONLY"]["maximum_drawdown_abs"]
        ),
        "delta_expected_shortfall": (
            metrics["D_REGIME_AND_CASCADE"]["expected_shortfall"]
            - metrics["B_EXISTING_REGIME_ONLY"]["expected_shortfall"]
        ),
        "delta_total_turnover": (
            metrics["D_REGIME_AND_CASCADE"]["total_turnover"]
            - metrics["B_EXISTING_REGIME_ONLY"]["total_turnover"]
        ),
        "missed_upside": float((-daily_increment).clip(lower=0.0).sum()),
        "avoided_loss": float(daily_increment.clip(lower=0.0).sum()),
        "reduced_exposure_days": int((d_gross < (b_gross - 1e-12)).sum()),
        **reentry,
    }
    receipts = _build_receipts(
        observations=observations_tuple,
        target_weights=weights,
        regime_controls=regime_controls,
        cascade_overlay=cascade_overlay,
        combined_cap=combined_cap,
        evidence_classification=evidence_classification,
        exit_rule=exit_rule,
    )

    report_body: dict[str, Any] = {
        "schema_version": "quant-financial-cascade-four-arm-report-v1",
        "module_id": "GV_FINANCIAL_CASCADE_FOUR_ARM",
        "evidence_classification": evidence_classification,
        "decision": (
            "ENGINEERING_COMPLETE_NO_ALPHA_AUTHORITY"
            if evidence_classification == ENGINEERING_ONLY
            else "GOVERNED_PIT_EVIDENCE_READY_FOR_PAPER_BRIDGE_REVIEW"
        ),
        "capital_authority": False,
        "score_uplift_authorized": False,
        "alpha_claim_authorized": False,
        "same_engine": "core.engine.run_simulation",
        "cost_rate": float(cost_rate),
        "portfolio_source_identity": dict(portfolio_source_identity),
        "combined_cap_formula": (
            "min(uncapped_portfolio_gross, regime_permitted_gross, "
            "cascade_permitted_gross)"
        ),
        "sequential_scalar_multiplication_used": False,
        "exit_rule": {
            "overlay_effective_date": exit_rule.overlay_effective_date,
            "evaluation_horizon_end_date": exit_rule.evaluation_horizon_end_date,
            "maximum_holding_period_sessions": (
                exit_rule.maximum_holding_period_sessions
            ),
            "manual_review_date": exit_rule.manual_review_date,
            "terminal_disposition": exit_rule.terminal_disposition,
            "reconciliation_date": exit_rule.reconciliation_date,
        },
        "arms": metrics,
        "incremental_d_vs_b": incremental,
        "prospective_receipts": receipts,
        "replay": {
            "exact_replay": exact_replay,
            "combined_target_weight_digest": _frame_digest(
                arm_weights["D_REGIME_AND_CASCADE"]
            ),
            "combined_simulation_digest": _frame_digest(
                simulations["D_REGIME_AND_CASCADE"]
            ),
        },
        "boundaries": {
            "security_selection_changed": False,
            "entry_exit_signal_changed": False,
            "intervention_ranking_used_for_trades": False,
            "command_center_required": False,
            "portfolio_mutation": False,
            "broker_or_live_capital": False,
        },
    }
    report_body["report_identity"] = _canonical_digest(report_body)
    return report_body
