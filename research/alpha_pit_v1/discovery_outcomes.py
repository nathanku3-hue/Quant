"""Discovery-only Alpha PIT v1 capability including fixture/label access.

This module is imported lazily by ``open_alpha_pit_session`` only for DISCOVERY.
Confirmatory and prospective capability objects therefore have no outcomes
method and need not load this module at all.
"""

from __future__ import annotations

from research.alpha_pit_v1.contracts import (
    FAMILY_ID,
    OUTCOME_COVERAGE_STATUSES,
    PRIMARY_LABEL_SPEC_ID,
    AlphaPITBackendV1,
    ArtifactRef,
    ResearchMode,
    validate_security_ids,
)
from research.alpha_pit_v1.manifests import verify_artifact_ref
from research.alpha_pit_v1.session import AlphaPITReadAPIv1


class AlphaPITDiscoveryAPIv1(AlphaPITReadAPIv1):
    """Read capability plus explicit labels, available only in DISCOVERY."""

    def __init__(
        self,
        *,
        family_id: str,
        decision_context_id: str,
        backend: AlphaPITBackendV1,
    ) -> None:
        self._initialize(
            mode=ResearchMode.DISCOVERY,
            family_id=family_id,
            decision_context_id=decision_context_id,
            backend=backend,
        )

    def outcomes(
        self,
        *,
        risk_set_id: str,
        label_spec_id: str = PRIMARY_LABEL_SPEC_ID,
    ) -> ArtifactRef:
        if label_spec_id != PRIMARY_LABEL_SPEC_ID:
            raise ValueError("alpha_pit_outcome_label_spec_invalid")
        if not str(risk_set_id).strip():
            raise ValueError("alpha_pit_outcome_risk_set_required")
        ref = self._backend.outcomes(
            risk_set_id=str(risk_set_id),
            label_spec_id=label_spec_id,
        )
        verify_artifact_ref(ref)
        if ref.artifact_type != "OUTCOMES":
            raise ValueError("alpha_pit_outcome_artifact_type_invalid")
        manifest = ref.manifest
        if manifest.get("family_id") != FAMILY_ID:
            raise ValueError("alpha_pit_outcome_manifest_family_invalid")
        if manifest.get("research_mode") != ResearchMode.DISCOVERY.value:
            raise ValueError("alpha_pit_outcome_manifest_mode_invalid")
        if manifest.get("financial_alpha_evidence") != 0:
            raise ValueError("alpha_pit_financial_alpha_evidence_must_be_zero")

        payload = ref.payload
        if not isinstance(payload, dict):
            raise ValueError("alpha_pit_outcome_payload_mapping_required")
        if payload.get("family_id") != FAMILY_ID:
            raise ValueError("alpha_pit_outcome_family_invalid")
        if payload.get("risk_set_id") != risk_set_id:
            raise ValueError("alpha_pit_outcome_risk_set_binding_invalid")
        if payload.get("label_spec_id") != label_spec_id:
            raise ValueError("alpha_pit_outcome_label_binding_invalid")
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise ValueError("alpha_pit_outcome_rows_required")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("alpha_pit_outcome_row_mapping_required")
            validate_security_ids([str(row.get("security_id") or "")])
            if row.get("risk_set_id") != risk_set_id or row.get("label_spec_id") != label_spec_id:
                raise ValueError("alpha_pit_outcome_row_binding_invalid")
            if str(row.get("coverage_status") or "") not in OUTCOME_COVERAGE_STATUSES:
                raise ValueError("alpha_pit_outcome_coverage_status_invalid")

        denominator = int(payload.get("risk_set_denominator", payload.get("denominator_count", -1)))
        finite = int(payload.get("finite_label_count", -1))
        missing = int(payload.get("missing_label_count", -1))
        if denominator < 0 or finite < 0 or missing < 0 or finite + missing != denominator:
            raise ValueError("alpha_pit_outcome_denominator_invalid")
        return ref
