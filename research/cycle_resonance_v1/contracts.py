"""Frozen narrow constants for the CYCLE_RESONANCE_v1 consumer."""

from __future__ import annotations

from research.alpha_pit_v1.contracts import (
    EXPECTATION_MEASURES,
    FAMILY_ID,
    OBSERVATION_FIELDS,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
)


INPUT_PACKET_SCHEMA = "cycle_resonance_input_packet_v1"
IMPLEMENTATION_MANIFEST_SCHEMA = "cycle_resonance_implementation_manifest_v1"
REQUESTED_OBSERVATION_FIELDS = OBSERVATION_FIELDS
REQUESTED_EXPECTATION_MEASURES = EXPECTATION_MEASURES
FIXTURE_AUTHORITY_CLASS = "MECHANICAL_FIXTURE_ZERO_EVIDENCE"
REAL_PIT_AUTHORITY_CLASS = "PIT_INPUT_PACKET"


def validate_family_constants() -> None:
    if FAMILY_ID != "CYCLE_RESONANCE_v1":
        raise ValueError("cycle_resonance_family_identity_invalid")
    if PRIMARY_LABEL_SPEC_ID != "CRV1_RIGHT_TAIL_252D_TOP5_V1":
        raise ValueError("cycle_resonance_primary_label_invalid")
    if RISK_SET_SPEC_ID != "CRV1_US_PRIMARY_COMMON_V1":
        raise ValueError("cycle_resonance_risk_set_spec_invalid")
