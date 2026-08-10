"""Compatibility shim for the W4 PREBREAKOUT Atlas.

Canonical W4 ownership lives in ``research.prebreakout_atlas_v1`` so W2/W5
package work cannot silently redefine Atlas methodology or census mechanics.
"""

from research.prebreakout_atlas_v1.atlas import (
    ATLAS_SCHEMA,
    DISCOVERY_AUTHORITY_CLASS,
    EXCLUDED_NONWINNER,
    EXCLUDED_WINNER,
    FALSE_WINNER,
    FAMILY_ID,
    FIXTURE_AUTHORITY_CLASS,
    MATCHED_CONTROL,
    MISSED_WINNER,
    ORDINARY_CONTROL_POOL,
    TRUE_WINNER,
    AtlasError,
    MatchedControlContract,
    PrebreakoutMethodologyBinding,
    assert_upstream_contract_alignment,
    build_discovery_atlas,
    upstream_contract_status,
    verify_discovery_atlas,
)

__all__ = [
    "ATLAS_SCHEMA",
    "DISCOVERY_AUTHORITY_CLASS",
    "EXCLUDED_NONWINNER",
    "EXCLUDED_WINNER",
    "FALSE_WINNER",
    "FAMILY_ID",
    "FIXTURE_AUTHORITY_CLASS",
    "MATCHED_CONTROL",
    "MISSED_WINNER",
    "ORDINARY_CONTROL_POOL",
    "TRUE_WINNER",
    "AtlasError",
    "MatchedControlContract",
    "PrebreakoutMethodologyBinding",
    "assert_upstream_contract_alignment",
    "build_discovery_atlas",
    "upstream_contract_status",
    "verify_discovery_atlas",
]
