from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from opportunity_engine.states import OpportunityState, ReasonCode


class SourceObservationClass(StrEnum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    INFERRED = "inferred"


ACTION_FIELD_NAMES = frozenset(
    {
        "alert",
        "alert_emitted",
        "broker_action",
        "broker_call",
        "buy_order",
        "sell_order",
        "order",
        "order_action",
        "score",
        "rank",
        "ranking",
        "candidate_rank",
        "signal_score",
    }
)


@dataclass(frozen=True)
class SignalEvidence:
    reason_code: ReasonCode
    source_class: SourceObservationClass
    source_name: str
    supports_transition: bool = True


@dataclass(frozen=True)
class TransitionEvidence:
    signals: tuple[SignalEvidence, ...]
    deterioration_evidence: bool = False
    thesis_broken: bool = False
    risk_approval: bool = False

    @property
    def reason_codes(self) -> frozenset[ReasonCode]:
        return frozenset(signal.reason_code for signal in self.signals)

    @property
    def source_classes(self) -> frozenset[SourceObservationClass]:
        return frozenset(signal.source_class for signal in self.signals)

    def has_observed_support(self) -> bool:
        return SourceObservationClass.OBSERVED in self.source_classes

    def all_sources_are(self, source_class: SourceObservationClass) -> bool:
        return bool(self.signals) and self.source_classes == frozenset({source_class})


@dataclass(frozen=True)
class TransitionRequest:
    current_state: OpportunityState
    requested_state: OpportunityState
    evidence: TransitionEvidence
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    resulting_state: OpportunityState
    reason: str
