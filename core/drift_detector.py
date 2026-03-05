"""
Phase 33: Drift Detection System - Core Engine

This module implements the cybernetic feedback loop that monitors the Alpha Engine's
financial reality against theoretical backtest expectations.

CEO Execution Invariants:
- Statistical Rigor: μ ± 2σ thresholds (not brittle percentages)
- Non-Blocking Telemetry: Async/batch, never block orchestrator
- Immutable Audit Trail: Append-only JSONL for forensic evidence

Divergence Taxonomy:
- ALLOCATION_DRIFT: Live positions deviate from backtest target weights
- REGIME_DRIFT: Live macro environment != backtest regime assumptions
- PARAMETER_DRIFT: Strategy config mutation (hash-based detection)
- SCHEDULE_DRIFT: Rebalance timing slippage or missed execution

FR-TBD: Drift detection as institutional standard (Renaissance/Two Sigma/Citadel)
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class DriftTaxonomy(str, Enum):
    """Binary classification of drift failure modes."""
    ALLOCATION_DRIFT = "ALLOCATION_DRIFT"
    REGIME_DRIFT = "REGIME_DRIFT"
    PARAMETER_DRIFT = "PARAMETER_DRIFT"
    SCHEDULE_DRIFT = "SCHEDULE_DRIFT"


@dataclass
class DriftResult:
    """
    Immutable snapshot of a drift detection event.

    Fields:
        drift_score: Statistical measure of divergence (sigma units from expected)
        taxonomy: Type of drift detected
        timestamp: UTC timestamp of detection
        alert_level: GREEN (in-range) | YELLOW (warning) | RED (alert)
        details: JSON-serializable dict with forensic context
        uid: Deterministic hash for deduplication
    """
    drift_score: float
    taxonomy: DriftTaxonomy
    timestamp: datetime
    alert_level: str  # "GREEN" | "YELLOW" | "RED"
    details: dict[str, Any]
    uid: str = field(default="")

    def __post_init__(self):
        """Generate deterministic UID if not provided."""
        if not self.uid:
            self.uid = self._generate_uid()

    def _generate_uid(self) -> str:
        """
        Phase 33 Step 1: Deterministic UID for forensic audit trail.

        Uses deterministic drift signal content only:
        - taxonomy
        - rounded drift_score
        - canonicalized details hash

        Timestamp is intentionally excluded so the same drift condition observed
        across cycles produces a stable UID for deduplication.
        """
        details_material = json.dumps(
            self.details,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        details_hash = hashlib.sha1(details_material.encode("utf-8")).hexdigest()

        immutable_fields = {
            "taxonomy": str(self.taxonomy),
            "drift_score": round(self.drift_score, 6),  # Round to avoid float precision drift
            "details_hash": details_hash,
        }
        material = json.dumps(immutable_fields, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(material.encode("utf-8")).hexdigest()

    def to_jsonl_record(self) -> str:
        """Serialize to JSONL format for append-only audit sink."""
        record = {
            "uid": self.uid,
            "timestamp": self.timestamp.isoformat(),
            "taxonomy": self.taxonomy.value,  # Use .value to get string value, not repr
            "drift_score": self.drift_score,
            "alert_level": self.alert_level,
            "details": self.details,
        }
        return json.dumps(record, separators=(",", ":"))


class DriftDetector:
    """
    Core drift detection engine with statistical comparison framework.

    Implements institutional best practices from KX Hedge Fund Analytics:
    "Identify divergence from expected behaviour before it impacts performance"
    """

    def __init__(
        self,
        sigma_threshold: float = 2.0,
        audit_dir: Path | None = None,
    ):
        """
        Initialize drift detector.

        Args:
            sigma_threshold: Statistical threshold for drift alerts (default: 2.0 sigma)
            audit_dir: Directory for JSONL audit trail (default: logs/drift/)
        """
        self.sigma_threshold = sigma_threshold
        self.audit_dir = audit_dir or Path("logs/drift")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def detect_allocation_drift(
        self,
        expected_weights: pd.Series,
        actual_weights: pd.Series,
        method: str = "chi2",
    ) -> DriftResult:
        """
        Phase 33 Step 1: Detect allocation drift using statistical comparison.

        Compares expected (backtest) vs actual (live) portfolio weights using:
        - Chi-squared goodness-of-fit test (default)
        - Kolmogorov-Smirnov test (alternative)

        Args:
            expected_weights: Backtest target weights (ticker -> weight)
            actual_weights: Live position weights (ticker -> weight)
            method: Statistical test ("chi2" or "ks")

        Returns:
            DriftResult with drift_score in sigma units
        """
        # Align series on common tickers (handle additions/deletions)
        common_tickers = expected_weights.index.intersection(actual_weights.index)

        if len(common_tickers) == 0:
            # Complete portfolio turnover - critical drift
            return self._create_drift_result(
                drift_score=10.0,  # Arbitrarily high sigma
                taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
                details={
                    "error": "No common tickers between expected and actual",
                    "expected_tickers": list(expected_weights.index),
                    "actual_tickers": list(actual_weights.index),
                },
            )

        expected_aligned = expected_weights.loc[common_tickers]
        actual_aligned = actual_weights.loc[common_tickers]

        # Normalize to handle partial overlap (weights sum to 1.0)
        expected_aligned = expected_aligned / expected_aligned.sum()
        actual_aligned = actual_aligned / actual_aligned.sum()

        # Statistical comparison
        if method == "chi2":
            drift_score, p_value = self._chi2_test(expected_aligned, actual_aligned)
        elif method == "ks":
            drift_score, p_value = self._ks_test(expected_aligned, actual_aligned)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Mean absolute deviation (MAD) for interpretability
        mad = np.abs(expected_aligned - actual_aligned).mean()

        return self._create_drift_result(
            drift_score=drift_score,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            details={
                "method": method,
                "p_value": float(p_value),
                "mean_abs_deviation": float(mad),
                "n_common_tickers": len(common_tickers),
                "n_expected_only": len(expected_weights) - len(common_tickers),
                "n_actual_only": len(actual_weights) - len(common_tickers),
                "top_deviations": self._top_deviations(expected_aligned, actual_aligned, n=5),
            },
        )

    def _chi2_test(
        self,
        expected: pd.Series,
        observed: pd.Series,
    ) -> tuple[float, float]:
        """
        Chi-squared goodness-of-fit test.

        Returns:
            (drift_score_sigma, p_value)
        """
        # Scale expected to match observed sum (chi2 requirement)
        expected_counts = expected * len(observed)
        observed_counts = observed * len(observed)

        # Avoid division by zero for very small weights
        mask = expected_counts > 1e-9
        expected_counts = expected_counts[mask]
        observed_counts = observed_counts[mask]

        if len(expected_counts) < 2:
            return 0.0, 1.0  # Not enough data for test

        chi2_stat, p_value = stats.chisquare(
            f_obs=observed_counts,
            f_exp=expected_counts,
        )

        # Convert chi2 statistic to sigma units (degrees of freedom = n - 1)
        df = len(expected_counts) - 1
        drift_score_sigma = np.sqrt(chi2_stat / df) if df > 0 else 0.0

        return drift_score_sigma, p_value

    def _ks_test(
        self,
        expected: pd.Series,
        observed: pd.Series,
    ) -> tuple[float, float]:
        """
        Kolmogorov-Smirnov test for distribution comparison.

        Returns:
            (drift_score_sigma, p_value)
        """
        # KS test requires cumulative distributions
        expected_sorted = expected.sort_values()
        observed_sorted = observed.sort_values()

        ks_stat, p_value = stats.ks_2samp(
            expected_sorted,
            observed_sorted,
        )

        # Convert KS statistic to approximate sigma units
        # KS ~ 1.36 / sqrt(n) for 2-sigma threshold
        n = len(expected)
        drift_score_sigma = ks_stat * np.sqrt(n) / 1.36

        return drift_score_sigma, p_value

    def _top_deviations(
        self,
        expected: pd.Series,
        actual: pd.Series,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """Return top N largest absolute weight deviations for forensic audit."""
        deviations = (actual - expected).abs().sort_values(ascending=False).head(n)
        return [
            {
                "ticker": ticker,
                "expected_weight": float(expected.loc[ticker]),
                "actual_weight": float(actual.loc[ticker]),
                "deviation": float(deviations.loc[ticker]),
            }
            for ticker in deviations.index
        ]

    def _create_drift_result(
        self,
        drift_score: float,
        taxonomy: DriftTaxonomy,
        details: dict[str, Any],
    ) -> DriftResult:
        """
        Create DriftResult with alert level based on sigma threshold.

        Alert Levels:
        - GREEN: drift_score < 1.0 sigma (in-range)
        - YELLOW: 1.0 <= drift_score < 2.0 sigma (warning)
        - RED: drift_score >= 2.0 sigma (alert)
        """
        if drift_score < 1.0:
            alert_level = "GREEN"
        elif drift_score < self.sigma_threshold:
            alert_level = "YELLOW"
        else:
            alert_level = "RED"

        return DriftResult(
            drift_score=drift_score,
            taxonomy=taxonomy,
            timestamp=datetime.now(timezone.utc),
            alert_level=alert_level,
            details=details,
        )

    def write_audit_trail(self, drift_result: DriftResult) -> None:
        """
        Phase 33 Step 1: Immutable audit trail (append-only JSONL).

        CEO Invariant: "If a strategy degrades, we need cryptographic proof of
        exactly what parameters were running at the time of failure."
        """
        date_str = drift_result.timestamp.strftime("%Y%m%d")
        audit_file = self.audit_dir / f"drift_events_{date_str}.jsonl"

        try:
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(drift_result.to_jsonl_record() + "\n")
            logging.info(
                "Drift event written to audit trail: uid=%s, taxonomy=%s, score=%.2f",
                drift_result.uid,
                drift_result.taxonomy,
                drift_result.drift_score,
            )
        except Exception as exc:
            logging.error("Failed to write drift audit trail: %s", exc)

    def validate_regime_state(
        self,
        expected_regime: dict[str, Any],
        live_macro: pd.DataFrame,
        live_regime_snapshot: dict[str, Any] | None = None,
        tolerance_days: int = 5,
        vix_spike_threshold: float = 35.0,
        bocpd_threshold: float = 0.80,
    ) -> DriftResult:
        """
        Phase 33 Step 2: Validate regime state consistency with tolerance thresholds.

        CEO Execution Invariant: "The REGIME_DRIFT detector must not trigger on a
        single-day macro spike. It must evaluate the snapshot against the expected
        backtest regime using a defined tolerance."

        Compares live macro features against backtest regime assumptions over a
        multi-day window to detect sustained regime shifts (not transient spikes).

        Args:
            expected_regime: Backtest regime snapshot (governor_state, target_exposure, bocpd_prob)
            live_macro: DataFrame with live macro features (last N days, must include date index)
            live_regime_snapshot: Optional pre-computed live regime state (from RegimeManager)
            tolerance_days: Grace period - only alert if divergence persists N days (default: 5)
            vix_spike_threshold: VIX level indicating stress regime (default: 35.0)
            bocpd_threshold: BOCPD probability threshold for changepoint detection (default: 0.80)

        Returns:
            DriftResult with REGIME_DRIFT taxonomy
        """
        if len(live_macro) < tolerance_days:
            return self._create_drift_result(
                drift_score=0.0,
                taxonomy=DriftTaxonomy.REGIME_DRIFT,
                details={
                    "error": f"Insufficient data for regime validation (need {tolerance_days} days)",
                    "available_days": len(live_macro),
                },
            )

        # Extract expected regime state from backtest
        expected_state = expected_regime.get("governor_state", expected_regime.get("state", "UNKNOWN"))
        expected_exposure = expected_regime.get("target_exposure", 1.0)
        expected_bocpd = expected_regime.get("bocpd_prob", 0.0)

        # If live_regime_snapshot provided, use it; otherwise compute from macro data
        if live_regime_snapshot:
            live_state = live_regime_snapshot.get("governor_state", "UNKNOWN")
            live_exposure = live_regime_snapshot.get("target_exposure", 1.0)
            live_bocpd = live_regime_snapshot.get("bocpd_prob", 0.0)
        else:
            # Fallback: Analyze live_macro directly (without RegimeManager)
            # This is a simplified heuristic-based validation
            live_state = self._infer_regime_state_from_macro(live_macro, tolerance_days)
            live_exposure = expected_exposure  # Assume no drift if RegimeManager unavailable
            live_bocpd = expected_bocpd

        # Compute drift score based on regime state divergence severity
        drift_score = 0.0
        drift_reasons = []

        # 1. State Mismatch (most critical)
        state_severity_map = {
            "RED": 3,
            "AMBER": 2,
            "GREEN": 1,
            "UNKNOWN": 0,
        }
        expected_severity = state_severity_map.get(expected_state, 0)
        live_severity = state_severity_map.get(live_state, 0)
        state_divergence = abs(live_severity - expected_severity)

        if state_divergence >= 2:
            # RED <-> GREEN transition (critical)
            drift_score += 3.0
            drift_reasons.append(
                f"Critical state divergence: expected {expected_state}, live {live_state}"
            )
        elif state_divergence == 1:
            # One-step transition (e.g., GREEN -> AMBER)
            drift_score += 1.0
            drift_reasons.append(
                f"Moderate state divergence: expected {expected_state}, live {live_state}"
            )

        # 2. Target Exposure Divergence
        exposure_diff = abs(live_exposure - expected_exposure)
        if exposure_diff > 0.30:
            # >30% exposure deviation (e.g., backtest expected 1.0x, live 0.5x)
            drift_score += 2.0
            drift_reasons.append(
                f"Large exposure divergence: expected {expected_exposure:.2f}, live {live_exposure:.2f}"
            )
        elif exposure_diff > 0.15:
            drift_score += 1.0
            drift_reasons.append(
                f"Moderate exposure divergence: expected {expected_exposure:.2f}, live {live_exposure:.2f}"
            )

        # 3. BOCPD Probability Breach (changepoint detection)
        if live_bocpd > bocpd_threshold and expected_bocpd < bocpd_threshold:
            drift_score += 1.5
            drift_reasons.append(
                f"BOCPD threshold breach: expected {expected_bocpd:.2f}, live {live_bocpd:.2f} > {bocpd_threshold}"
            )

        # 4. VIX Spike Detection (market stress indicator)
        if "vix_level" in live_macro.columns or "vix_proxy" in live_macro.columns:
            vix_col = "vix_level" if "vix_level" in live_macro.columns else "vix_proxy"
            recent_vix = live_macro[vix_col].tail(tolerance_days)
            mean_recent_vix = recent_vix.mean()

            if mean_recent_vix > vix_spike_threshold:
                # Sustained high VIX (averaged over tolerance_days)
                drift_score += 2.0
                drift_reasons.append(
                    f"Sustained VIX spike: {mean_recent_vix:.1f} > {vix_spike_threshold} "
                    f"(averaged over {tolerance_days} days)"
                )
            elif recent_vix.max() > vix_spike_threshold and recent_vix.tail(1).values[0] > vix_spike_threshold:
                # Recent VIX spike still active (not transient)
                drift_score += 1.0
                drift_reasons.append(
                    f"Active VIX spike: current {recent_vix.tail(1).values[0]:.1f} > {vix_spike_threshold}"
                )

        # If no divergence detected, provide confirmation
        if drift_score == 0.0:
            drift_reasons.append("No regime drift detected - live state matches backtest assumptions")

        details = {
            "expected_state": expected_state,
            "live_state": live_state,
            "expected_exposure": expected_exposure,
            "live_exposure": live_exposure,
            "expected_bocpd": expected_bocpd,
            "live_bocpd": live_bocpd,
            "state_divergence_steps": int(state_divergence),
            "exposure_divergence": float(exposure_diff),
            "tolerance_days": tolerance_days,
            "drift_reasons": drift_reasons,
        }

        # Add VIX statistics if available
        if "vix_level" in live_macro.columns or "vix_proxy" in live_macro.columns:
            vix_col = "vix_level" if "vix_level" in live_macro.columns else "vix_proxy"
            recent_vix = live_macro[vix_col].tail(tolerance_days)
            details["vix_mean"] = float(recent_vix.mean())
            details["vix_max"] = float(recent_vix.max())
            details["vix_current"] = float(recent_vix.tail(1).values[0])

        return self._create_drift_result(
            drift_score=drift_score,
            taxonomy=DriftTaxonomy.REGIME_DRIFT,
            details=details,
        )

    @staticmethod
    def _infer_regime_state_from_macro(
        live_macro: pd.DataFrame,
        window: int = 5,
    ) -> str:
        """
        Fallback heuristic for inferring regime state from macro data.

        Used when RegimeManager snapshot is unavailable. Applies simplified
        stress detection rules based on VIX and credit freeze indicators.
        """
        recent_data = live_macro.tail(window)

        # Check for RED regime indicators
        if "vix_level" in recent_data.columns or "vix_proxy" in recent_data.columns:
            vix_col = "vix_level" if "vix_level" in recent_data.columns else "vix_proxy"
            mean_vix = recent_data[vix_col].mean()

            if mean_vix > 40.0:
                return "RED"  # Crisis regime
            elif mean_vix > 25.0:
                return "AMBER"  # Elevated volatility

        # Check credit freeze indicator
        if "credit_freeze" in recent_data.columns:
            if recent_data["credit_freeze"].any():
                return "RED"

        # Default: assume GREEN (stable regime)
        return "GREEN"

    def detect_parameter_drift(
        self,
        backtest_config: dict[str, Any],
        live_config: dict[str, Any],
    ) -> DriftResult:
        """
        Phase 33 Step 3: Detect strategy parameter mutations.

        Uses hash-based comparison to detect if live execution uses different
        parameters than backtest specification.

        Args:
            backtest_config: Strategy config from backtest run metadata
            live_config: Strategy config from current live execution

        Returns:
            DriftResult with PARAMETER_DRIFT taxonomy
        """
        backtest_hash = self._config_hash(backtest_config)
        live_hash = self._config_hash(live_config)

        if backtest_hash == live_hash:
            # No parameter drift
            return self._create_drift_result(
                drift_score=0.0,
                taxonomy=DriftTaxonomy.PARAMETER_DRIFT,
                details={
                    "status": "MATCH",
                    "config_hash": backtest_hash,
                },
            )

        # Parameter drift detected - compute which parameters changed
        changed_params = self._diff_configs(backtest_config, live_config)

        # Drift score = number of changed parameters (simple heuristic)
        drift_score = float(len(changed_params))

        return self._create_drift_result(
            drift_score=drift_score,
            taxonomy=DriftTaxonomy.PARAMETER_DRIFT,
            details={
                "status": "MISMATCH",
                "backtest_hash": backtest_hash,
                "live_hash": live_hash,
                "changed_parameters": changed_params,
                "n_changed": len(changed_params),
            },
        )

    def _config_hash(self, config: dict[str, Any]) -> str:
        """Deterministic hash of strategy configuration."""
        material = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def _diff_configs(
        self,
        backtest_config: dict[str, Any],
        live_config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return list of changed parameters with before/after values."""
        changed = []

        # Check all keys in backtest config
        for key, backtest_value in backtest_config.items():
            live_value = live_config.get(key)
            if live_value != backtest_value:
                changed.append({
                    "parameter": key,
                    "backtest_value": backtest_value,
                    "live_value": live_value,
                })

        # Check for new keys in live config (not in backtest)
        for key in live_config:
            if key not in backtest_config:
                changed.append({
                    "parameter": key,
                    "backtest_value": None,
                    "live_value": live_config[key],
                })

        return changed

    def track_rebalance_compliance(
        self,
        expected_schedule: list[datetime],
        actual_trades: pd.DataFrame,
        tolerance_hours: float = 4.0,
    ) -> DriftResult:
        """
        Phase 33 Step 4: Track rebalance schedule compliance.

        Compares scheduled rebalance dates vs actual trade execution timestamps.
        Measures execution timing slippage.

        Args:
            expected_schedule: List of planned rebalance datetimes
            actual_trades: DataFrame with actual trade execution (must have 'timestamp' column)
            tolerance_hours: Acceptable delay before flagging slippage

        Returns:
            DriftResult with SCHEDULE_DRIFT taxonomy
        """
        if "timestamp" not in actual_trades.columns:
            return self._create_drift_result(
                drift_score=0.0,
                taxonomy=DriftTaxonomy.SCHEDULE_DRIFT,
                details={
                    "error": "Missing 'timestamp' column in actual_trades DataFrame",
                },
            )

        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(actual_trades["timestamp"]):
            actual_trades = actual_trades.copy()
            actual_trades["timestamp"] = pd.to_datetime(actual_trades["timestamp"])

        missed_rebalances = []
        slippage_events = []

        for scheduled_dt in expected_schedule:
            # Find trades within tolerance window
            tolerance_delta = pd.Timedelta(hours=tolerance_hours)
            window_start = scheduled_dt - tolerance_delta
            window_end = scheduled_dt + tolerance_delta

            trades_in_window = actual_trades[
                (actual_trades["timestamp"] >= window_start) &
                (actual_trades["timestamp"] <= window_end)
            ]

            if len(trades_in_window) == 0:
                # Missed rebalance
                missed_rebalances.append(scheduled_dt.isoformat())
            else:
                # Measure slippage (time delta from scheduled)
                actual_dt = trades_in_window["timestamp"].iloc[0]
                slippage_seconds = (actual_dt - scheduled_dt).total_seconds()
                slippage_events.append({
                    "scheduled": scheduled_dt.isoformat(),
                    "actual": actual_dt.isoformat(),
                    "slippage_seconds": float(slippage_seconds),
                })

        # Drift score: number of missed rebalances
        drift_score = float(len(missed_rebalances))

        return self._create_drift_result(
            drift_score=drift_score,
            taxonomy=DriftTaxonomy.SCHEDULE_DRIFT,
            details={
                "expected_rebalances": len(expected_schedule),
                "missed_rebalances": len(missed_rebalances),
                "missed_dates": missed_rebalances,
                "slippage_events": slippage_events,
                "mean_slippage_seconds": float(np.mean([e["slippage_seconds"] for e in slippage_events])) if slippage_events else 0.0,
            },
        )


# Module-level convenience function
def create_drift_detector(sigma_threshold: float = 2.0) -> DriftDetector:
    """Factory function for creating DriftDetector with default settings."""
    return DriftDetector(sigma_threshold=sigma_threshold)
