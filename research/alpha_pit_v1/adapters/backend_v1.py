"""Concrete first-family backend composition for Alpha PIT v1.

This is intentionally not a provider registry.  CRV1 has exactly one structured
CIQ producer and one SEC/company-filing claims producer.  Discovery outcomes
remain a separate capability and are not implemented here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from research.alpha_pit_v1.adapters.ciq_cycle_v1 import CiqCycleV1Adapter
from research.alpha_pit_v1.adapters.sec_claims_v1 import SecAlphaClaimsV1Adapter
from research.alpha_pit_v1.contracts import (
    AlphaPITBackendV1,
    AlphaPITContractError,
    ArtifactRef,
    ResearchMode,
)


class CycleResonancePITBackendV1(AlphaPITBackendV1):
    """Frozen CRV1 producer composition: CIQ structured + SEC claims."""

    def __init__(
        self,
        *,
        ciq: CiqCycleV1Adapter,
        sec_claims: SecAlphaClaimsV1Adapter,
    ) -> None:
        if not isinstance(ciq, CiqCycleV1Adapter):
            raise TypeError("alpha_pit_ciq_cycle_v1_adapter_required")
        if not isinstance(sec_claims, SecAlphaClaimsV1Adapter):
            raise TypeError("alpha_pit_sec_claims_v1_adapter_required")
        self._ciq = ciq
        self._sec_claims = sec_claims

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        return self._ciq.risk_set(as_of=as_of, research_mode=research_mode)

    def observations(
        self,
        *,
        ids: Sequence[str],
        fields: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        return self._ciq.observations(ids=ids, fields=fields, as_of=as_of, research_mode=research_mode)

    def source_claims(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        return self._sec_claims.source_claims(ids=ids, as_of=as_of, research_mode=research_mode)

    def expectations(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        return self._ciq.expectations(ids=ids, as_of=as_of, research_mode=research_mode)

    def outcomes(self, *, risk_set_id: str, label_spec_id: str) -> ArtifactRef:
        raise AlphaPITContractError("alpha_pit_outcome_backend_not_attached_to_crv1_read_backend")
