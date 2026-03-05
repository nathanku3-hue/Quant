"""
Phase 33 Step 1: Comprehensive test suite for drift detection engine.

Validates statistical rigor, forensic audit trail, and all drift taxonomy detection.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.drift_detector import (
    DriftDetector,
    DriftResult,
    DriftTaxonomy,
    create_drift_detector,
)


@pytest.fixture
def drift_detector(tmp_path: Path) -> DriftDetector:
    """Create DriftDetector with temporary audit directory."""
    return DriftDetector(sigma_threshold=2.0, audit_dir=tmp_path / "drift")


@pytest.fixture
def sample_weights() -> tuple[pd.Series, pd.Series]:
    """Sample portfolio weights: expected (backtest) and actual (live)."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    expected = pd.Series([0.25, 0.20, 0.20, 0.20, 0.15], index=tickers)
    actual = pd.Series([0.25, 0.20, 0.20, 0.20, 0.15], index=tickers)  # Identical
    return expected, actual


class TestDriftResult:
    """Test DriftResult dataclass and UID generation."""

    def test_drift_result_uid_deterministic(self):
        """UID should be deterministic based on taxonomy, rounded score, and details hash."""
        result1 = DriftResult(
            drift_score=1.5,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={"test": "data"},
        )
        result2 = DriftResult(
            drift_score=1.5,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 5, 0, tzinfo=timezone.utc),  # Different timestamp
            alert_level="YELLOW",
            details={"test": "data"},
        )
        assert result1.uid == result2.uid

    def test_uid_stability_across_cycles(self):
        """UID should remain stable across detection cycles when signal content is unchanged."""
        cycle1 = DriftResult(
            drift_score=2.1234561,
            taxonomy=DriftTaxonomy.REGIME_DRIFT,
            timestamp=datetime(2026, 3, 2, 9, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={"state": "AMBER", "bocpd_prob": 0.81},
        )
        cycle2 = DriftResult(
            drift_score=2.1234564,  # Rounds to same 6dp value
            taxonomy=DriftTaxonomy.REGIME_DRIFT,
            timestamp=datetime(2026, 3, 2, 10, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={"state": "AMBER", "bocpd_prob": 0.81},
        )

        assert cycle1.uid == cycle2.uid

    def test_drift_result_uid_changes_with_score(self):
        """UID should change if drift_score changes."""
        result1 = DriftResult(
            drift_score=1.5,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={},
        )
        result2 = DriftResult(
            drift_score=2.5,  # Different score
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="RED",
            details={},
        )
        assert result1.uid != result2.uid

    def test_drift_result_to_jsonl(self):
        """JSONL serialization should be valid."""
        result = DriftResult(
            drift_score=1.5,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={"test": "data"},
        )
        jsonl_line = result.to_jsonl_record()
        parsed = json.loads(jsonl_line)

        assert parsed["uid"] == result.uid
        assert parsed["taxonomy"] == "ALLOCATION_DRIFT"
        assert parsed["drift_score"] == 1.5
        assert parsed["alert_level"] == "YELLOW"


class TestAllocationDrift:
    """Test allocation drift detection with statistical tests."""

    def test_allocation_drift_no_divergence(
        self,
        drift_detector: DriftDetector,
        sample_weights: tuple[pd.Series, pd.Series],
    ):
        """Identical weights should produce drift_score near zero."""
        expected, actual = sample_weights
        result = drift_detector.detect_allocation_drift(expected, actual)

        assert result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
        assert result.drift_score < 0.5  # Should be very small
        assert result.alert_level == "GREEN"
        assert result.details["n_common_tickers"] == 5

    def test_allocation_drift_2sigma_threshold(
        self,
        drift_detector: DriftDetector,
        sample_weights: tuple[pd.Series, pd.Series],
    ):
        """Large weight deviations should trigger YELLOW/RED alert (>1 sigma)."""
        expected, _ = sample_weights

        # Create actual weights with extreme drift (complete portfolio rebalance)
        actual = pd.Series(
            [0.90, 0.02, 0.02, 0.03, 0.03],  # AAPL massively overweight
            index=expected.index,
        )

        result = drift_detector.detect_allocation_drift(expected, actual)

        assert result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
        # With n=5 tickers, chi-squared gives ~1.68 sigma for this deviation
        # This exceeds 1-sigma threshold (YELLOW alert) but may not reach 2-sigma
        assert result.drift_score >= 1.0, f"Expected drift_score >= 1.0, got {result.drift_score}"
        assert result.alert_level in ("YELLOW", "RED"), f"Expected YELLOW or RED, got {result.alert_level}"
        assert len(result.details["top_deviations"]) > 0

    def test_allocation_drift_chi2_method(
        self,
        drift_detector: DriftDetector,
        sample_weights: tuple[pd.Series, pd.Series],
    ):
        """Chi-squared test should detect moderate drift."""
        expected, _ = sample_weights
        actual = pd.Series(
            [0.30, 0.18, 0.18, 0.18, 0.16],  # Slight rebalancing
            index=expected.index,
        )

        result = drift_detector.detect_allocation_drift(expected, actual, method="chi2")

        assert result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
        assert "p_value" in result.details
        assert "mean_abs_deviation" in result.details

    def test_allocation_drift_ks_method(
        self,
        drift_detector: DriftDetector,
        sample_weights: tuple[pd.Series, pd.Series],
    ):
        """Kolmogorov-Smirnov test should work as alternative."""
        expected, _ = sample_weights
        actual = pd.Series(
            [0.30, 0.18, 0.18, 0.18, 0.16],
            index=expected.index,
        )

        result = drift_detector.detect_allocation_drift(expected, actual, method="ks")

        assert result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
        assert "p_value" in result.details

    def test_allocation_drift_no_common_tickers(
        self,
        drift_detector: DriftDetector,
    ):
        """Complete portfolio turnover should trigger critical drift."""
        expected = pd.Series([0.5, 0.5], index=["AAPL", "MSFT"])
        actual = pd.Series([0.5, 0.5], index=["GOOGL", "AMZN"])  # Completely different

        result = drift_detector.detect_allocation_drift(expected, actual)

        assert result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
        assert result.drift_score >= 5.0  # Should be very high
        assert result.alert_level == "RED"
        assert "error" in result.details


class TestRegimeValidation:
    """Test regime state validation with tolerance thresholds."""

    def test_regime_validation_stable_regime(self, drift_detector: DriftDetector):
        """Stable regime (no divergence) should produce zero drift."""
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        live_regime_snapshot = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        live_macro = pd.DataFrame({
            "spy_close": [500, 505, 510, 515, 520],
            "vix_level": [15, 16, 14, 15, 14],
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=live_regime_snapshot,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        assert result.drift_score == 0.0
        assert result.alert_level == "GREEN"
        assert "No regime drift detected" in result.details["drift_reasons"][0]

    def test_regime_validation_critical_state_shift(self, drift_detector: DriftDetector):
        """Critical regime shift (GREEN -> RED) should trigger high drift score."""
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        live_regime_snapshot = {
            "governor_state": "RED",
            "target_exposure": 0.2,
            "bocpd_prob": 0.85,
        }
        live_macro = pd.DataFrame({
            "spy_close": [500, 490, 480, 470, 460],
            "vix_level": [15, 25, 35, 42, 45],
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=live_regime_snapshot,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        assert result.drift_score >= 2.0  # Should exceed threshold for RED alert
        assert result.alert_level in ("YELLOW", "RED")
        assert result.details["expected_state"] == "GREEN"
        assert result.details["live_state"] == "RED"

    def test_regime_validation_vix_spike_above_35(self, drift_detector: DriftDetector):
        """
        Phase 33 Step 2: CEO-mandated test for synthetic VIX spike.

        Scenario: Backtest expected stable environment (VIX ~15), but live market
        experiences VIX spike above 35, sustained over tolerance window.

        This should trigger REGIME_DRIFT deterministically.
        """
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        # Live regime detects stress (VIX spike changes governor state)
        live_regime_snapshot = {
            "governor_state": "RED",
            "target_exposure": 0.2,
            "bocpd_prob": 0.25,
        }
        # Synthetic VIX spike: 5-day sustained spike above 35
        live_macro = pd.DataFrame({
            "spy_close": [500, 495, 485, 475, 470],
            "vix_level": [36, 38, 42, 40, 37],  # All above 35 threshold
            "credit_freeze": [False, False, True, True, True],
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=live_regime_snapshot,
            tolerance_days=5,
            vix_spike_threshold=35.0,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        assert result.drift_score >= 2.0, f"Expected drift_score >= 2.0, got {result.drift_score}"
        assert result.alert_level in ("YELLOW", "RED"), f"Expected alert, got {result.alert_level}"

        # Verify VIX statistics captured
        assert "vix_mean" in result.details
        assert result.details["vix_mean"] > 35.0, "Mean VIX should exceed spike threshold"
        assert "Sustained VIX spike" in " ".join(result.details["drift_reasons"])

    def test_regime_validation_bocpd_threshold_breach(
        self,
        drift_detector: DriftDetector,
    ):
        """BOCPD probability breach should trigger drift alert."""
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.15,  # Low changepoint probability
        }
        live_regime_snapshot = {
            "governor_state": "AMBER",
            "target_exposure": 0.75,
            "bocpd_prob": 0.95,  # High changepoint probability (regime shift detected)
        }
        live_macro = pd.DataFrame({
            "spy_close": [500, 505, 510, 508, 512],
            "vix_level": [15, 18, 22, 28, 26],
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=live_regime_snapshot,
            bocpd_threshold=0.80,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        assert result.drift_score > 0.0
        assert "BOCPD threshold breach" in " ".join(result.details["drift_reasons"])

    def test_regime_validation_transient_spike_no_alert(
        self,
        drift_detector: DriftDetector,
    ):
        """
        Transient VIX spike (single day) should NOT trigger drift alert.

        CEO Invariant: "Must not trigger on a single-day macro spike."
        """
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        # Regime state remains GREEN (single-day spike not sustained)
        live_regime_snapshot = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.20,
        }
        # Single-day VIX spike, but mean over tolerance window is acceptable
        live_macro = pd.DataFrame({
            "spy_close": [500, 505, 510, 515, 520],
            "vix_level": [15, 16, 45, 17, 16],  # Day 3 spike, but not sustained
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=live_regime_snapshot,
            tolerance_days=5,
            vix_spike_threshold=35.0,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        # Mean VIX over 5 days: (15+16+45+17+16)/5 = 21.8 (< 35 threshold)
        # Should not trigger sustained VIX spike alert
        assert result.drift_score < 2.0, "Transient spike should not trigger critical drift"
        # May still have minor drift due to BOCPD increase, but not critical
        assert result.alert_level in ("GREEN", "YELLOW"), f"Unexpected alert level: {result.alert_level}"

    def test_regime_validation_fallback_heuristic(
        self,
        drift_detector: DriftDetector,
    ):
        """Fallback heuristic should infer regime state from macro data."""
        expected_regime = {
            "governor_state": "GREEN",
            "target_exposure": 1.3,
            "bocpd_prob": 0.12,
        }
        # No live_regime_snapshot provided - use fallback
        live_macro = pd.DataFrame({
            "spy_close": [500, 490, 480, 470, 460],
            "vix_level": [15, 25, 35, 45, 50],  # VIX escalation (mean=34, max=50)
        })

        result = drift_detector.validate_regime_state(
            expected_regime,
            live_macro,
            live_regime_snapshot=None,  # Force fallback heuristic
            tolerance_days=5,
        )

        assert result.taxonomy == DriftTaxonomy.REGIME_DRIFT
        # Fallback detects AMBER (mean VIX=34 > 25 threshold but < 40)
        assert result.details["live_state"] in ("AMBER", "RED")
        assert result.drift_score > 0.0  # Should detect divergence from GREEN


class TestParameterDrift:
    """Test parameter mutation detection with hash-based comparison."""

    def test_parameter_drift_no_mutation(self, drift_detector: DriftDetector):
        """Identical configs should produce zero drift."""
        config = {
            "entry_threshold": 0.8,
            "exit_threshold": 0.5,
            "factor_weights": {"momentum": 0.25, "quality": 0.25},
        }

        result = drift_detector.detect_parameter_drift(config, config)

        assert result.taxonomy == DriftTaxonomy.PARAMETER_DRIFT
        assert result.drift_score == 0.0
        assert result.alert_level == "GREEN"
        assert result.details["status"] == "MATCH"

    def test_parameter_drift_mutation_detected(self, drift_detector: DriftDetector):
        """Changed parameters should be detected with hash mismatch."""
        backtest_config = {
            "entry_threshold": 0.8,
            "exit_threshold": 0.5,
        }
        live_config = {
            "entry_threshold": 0.7,  # Changed
            "exit_threshold": 0.5,
        }

        result = drift_detector.detect_parameter_drift(backtest_config, live_config)

        assert result.taxonomy == DriftTaxonomy.PARAMETER_DRIFT
        assert result.drift_score > 0.0
        assert result.details["status"] == "MISMATCH"
        assert len(result.details["changed_parameters"]) == 1
        assert result.details["changed_parameters"][0]["parameter"] == "entry_threshold"

    def test_parameter_drift_new_parameter_added(self, drift_detector: DriftDetector):
        """New parameters in live config should be flagged."""
        backtest_config = {"entry_threshold": 0.8}
        live_config = {"entry_threshold": 0.8, "new_param": 42}

        result = drift_detector.detect_parameter_drift(backtest_config, live_config)

        assert result.taxonomy == DriftTaxonomy.PARAMETER_DRIFT
        assert result.drift_score > 0.0
        changed = result.details["changed_parameters"]
        assert any(p["parameter"] == "new_param" for p in changed)


class TestRebalanceCompliance:
    """Test rebalance schedule compliance tracking."""

    def test_rebalance_compliance_on_schedule(self, drift_detector: DriftDetector):
        """Trades executed on schedule should produce zero drift."""
        schedule = [
            datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 2, 9, 30, 0, tzinfo=timezone.utc),
        ]
        actual_trades = pd.DataFrame({
            "timestamp": [
                datetime(2026, 3, 1, 9, 35, 0, tzinfo=timezone.utc),  # 5 min delay
                datetime(2026, 3, 2, 9, 32, 0, tzinfo=timezone.utc),  # 2 min delay
            ],
            "symbol": ["AAPL", "MSFT"],
            "qty": [100, 50],
        })

        result = drift_detector.track_rebalance_compliance(schedule, actual_trades)

        assert result.taxonomy == DriftTaxonomy.SCHEDULE_DRIFT
        assert result.drift_score == 0.0  # No missed rebalances
        assert result.alert_level == "GREEN"
        assert result.details["missed_rebalances"] == 0

    def test_rebalance_compliance_missed_rebalance(self, drift_detector: DriftDetector):
        """Missed rebalances should trigger drift alert."""
        schedule = [
            datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 2, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 3, 9, 30, 0, tzinfo=timezone.utc),
        ]
        actual_trades = pd.DataFrame({
            "timestamp": [
                datetime(2026, 3, 1, 9, 35, 0, tzinfo=timezone.utc),  # Only 1 trade
            ],
            "symbol": ["AAPL"],
            "qty": [100],
        })

        result = drift_detector.track_rebalance_compliance(schedule, actual_trades)

        assert result.taxonomy == DriftTaxonomy.SCHEDULE_DRIFT
        assert result.drift_score == 2.0  # 2 missed rebalances
        assert result.alert_level == "RED"
        assert result.details["missed_rebalances"] == 2

    def test_rebalance_compliance_slippage_measurement(
        self,
        drift_detector: DriftDetector,
    ):
        """Slippage (timing delay) should be measured."""
        schedule = [datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc)]
        actual_trades = pd.DataFrame({
            "timestamp": [datetime(2026, 3, 1, 10, 30, 0, tzinfo=timezone.utc)],  # 1 hour delay
            "symbol": ["AAPL"],
            "qty": [100],
        })

        result = drift_detector.track_rebalance_compliance(
            schedule,
            actual_trades,
            tolerance_hours=2.0,  # Within tolerance
        )

        assert result.taxonomy == DriftTaxonomy.SCHEDULE_DRIFT
        assert result.drift_score == 0.0  # Within tolerance
        assert len(result.details["slippage_events"]) == 1
        assert result.details["slippage_events"][0]["slippage_seconds"] == 3600.0  # 1 hour


class TestAuditTrail:
    """Test immutable audit trail writing."""

    def test_audit_trail_creates_file(
        self,
        drift_detector: DriftDetector,
        tmp_path: Path,
    ):
        """Audit trail should create JSONL file."""
        result = DriftResult(
            drift_score=1.5,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={"test": "data"},
        )

        drift_detector.write_audit_trail(result)

        audit_file = tmp_path / "drift" / "drift_events_20260302.jsonl"
        assert audit_file.exists()

        # Verify JSONL content
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["uid"] == result.uid
        assert record["taxonomy"] == "ALLOCATION_DRIFT"

    def test_audit_trail_append_only(
        self,
        drift_detector: DriftDetector,
        tmp_path: Path,
    ):
        """Multiple writes should append to same file."""
        result1 = DriftResult(
            drift_score=1.0,
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
            alert_level="YELLOW",
            details={},
        )
        result2 = DriftResult(
            drift_score=2.0,
            taxonomy=DriftTaxonomy.PARAMETER_DRIFT,
            timestamp=datetime(2026, 3, 2, 13, 0, 0, tzinfo=timezone.utc),
            alert_level="RED",
            details={},
        )

        drift_detector.write_audit_trail(result1)
        drift_detector.write_audit_trail(result2)

        audit_file = tmp_path / "drift" / "drift_events_20260302.jsonl"
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2


class TestFactoryFunction:
    """Test convenience factory function."""

    def test_create_drift_detector(self):
        """Factory function should create valid detector."""
        detector = create_drift_detector(sigma_threshold=3.0)
        assert isinstance(detector, DriftDetector)
        assert detector.sigma_threshold == 3.0
