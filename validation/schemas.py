from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from data.provenance import ProvenanceError
from data.provenance import assert_can_promote
from data.provenance import require_source_quality
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import utc_now_iso
from data.provenance import validate_manifest
from validation.bootstrap import run_bootstrap_ci
from validation.oos import run_oos_test
from validation.permutation import run_permutation_test
from validation.regime_tests import run_regime_tests
from validation.walk_forward import run_walk_forward


VALIDATION_REPORT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ValidationReport:
    strategy_id: str
    source_manifest: dict[str, Any]
    generated_at_utc: str
    oos: dict[str, Any]
    walk_forward: dict[str, Any]
    regime: dict[str, Any]
    permutation: dict[str, Any]
    bootstrap: dict[str, Any]
    promotion_intent: bool = False
    schema_version: str = VALIDATION_REPORT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "generated_at_utc": self.generated_at_utc,
            "promotion_intent": bool(self.promotion_intent),
            "source_manifest": dict(self.source_manifest),
            "oos": dict(self.oos),
            "walk_forward": dict(self.walk_forward),
            "regime": dict(self.regime),
            "permutation": dict(self.permutation),
            "bootstrap": dict(self.bootstrap),
            "passed": bool(
                self.oos.get("passed")
                and self.walk_forward.get("passed")
                and self.regime.get("passed")
                and self.permutation.get("passed")
                and self.bootstrap.get("passed")
            ),
        }


def validate_validation_report(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise ProvenanceError("validation report must be a dictionary")
    manifest = report.get("source_manifest")
    if not isinstance(manifest, dict):
        raise ProvenanceError("validation report requires source_manifest")
    validate_manifest(manifest)
    if bool(report.get("promotion_intent")):
        require_source_quality(
            manifest,
            {SOURCE_QUALITY_CANONICAL},
            context="V1 promotion validation report",
        )
        assert_can_promote({"manifest": manifest})
    for section in ("oos", "walk_forward", "regime", "permutation", "bootstrap"):
        if not isinstance(report.get(section), dict):
            raise ProvenanceError(f"validation report missing section: {section}")


def run_minimal_validation_lab(
    frame: pd.DataFrame,
    *,
    source_manifest: dict[str, Any],
    strategy_id: str,
    return_col: str = "net_ret",
    promotion_intent: bool = False,
) -> ValidationReport:
    validate_manifest(source_manifest)
    if promotion_intent:
        require_source_quality(
            source_manifest,
            {SOURCE_QUALITY_CANONICAL},
            context="V1 promotion validation lab",
        )
    report = ValidationReport(
        strategy_id=strategy_id,
        source_manifest=dict(source_manifest),
        generated_at_utc=utc_now_iso(),
        oos=run_oos_test(frame, return_col=return_col),
        walk_forward=run_walk_forward(frame, return_col=return_col),
        regime=run_regime_tests(frame, return_col=return_col),
        permutation=run_permutation_test(frame, return_col=return_col),
        bootstrap=run_bootstrap_ci(frame, return_col=return_col),
        promotion_intent=bool(promotion_intent),
    )
    validate_validation_report(report.to_dict())
    return report

