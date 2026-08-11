"""OK-SBI-0 QSourceContractV1 — outcome-blind numeric Q source binding.

RevGrowth_12m + ROIC is a conceptual candidate only.  This module never invents
fields, never silent-bridges unavailable primitives, and never opens outcomes.
Binding requires an exact field map for every primitive; incomplete maps yield
one of the four legal feasibility verdicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


SLICE_ID = "OK-SBI-0"
CONTRACT_ID = "QSourceContractV1"
SPEC_VERSION = "v1.2"
MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES = 1

Q_GF_BOUND = "Q_GF_BOUND"
Q_MINIMAL_AMENDMENT_REQUIRED = "Q_MINIMAL_AMENDMENT_REQUIRED"
Q_AMENDED_BOUND = "Q_AMENDED_BOUND"
Q_SOURCE_BLOCKED = "Q_SOURCE_BLOCKED"

LEGAL_VERDICTS = frozenset(
    {
        Q_GF_BOUND,
        Q_MINIMAL_AMENDMENT_REQUIRED,
        Q_AMENDED_BOUND,
        Q_SOURCE_BLOCKED,
    }
)

REQUIRED_PRIMITIVE_FIELDS = (
    "primitive_id",
    "provider_source_object",
    "exact_field_identifier",
    "ciqsec_trading_item_identity",
    "period_perspective_semantics",
    "pit_availability_timestamp",
    "minimum_publication_processing_lag",
    "unit_currency_law",
    "formula_denominator",
    "restatement_carry_law",
    "applicability_rule",
    "missingness_reason",
    "corporate_action_treatment",
    "source_receipt_hash",
    "no_bridge_proof",
)

_BLOCKED_TOKENS = frozenset(
    {
        "",
        "BLOCKED_UNSET",
        "TBD",
        "NULL",
        "PLACEHOLDER",
        "UNHASHED",
        "UNLANDED",
        "NONE",
        "N/A",
        "CONCEPTUAL_ONLY",
    }
)

# Conceptual candidate only — not authority until every field is source-bound.
CONCEPTUAL_CANDIDATE_PRIMITIVES: tuple[dict[str, str], ...] = (
    {
        "primitive_id": "RevGrowth_12m",
        "provider_source_object": "CONCEPTUAL_ONLY",
        "exact_field_identifier": "BLOCKED_UNSET",
        "ciqsec_trading_item_identity": "CIQSEC+trading_item required; unbound",
        "period_perspective_semantics": "BLOCKED_UNSET",
        "pit_availability_timestamp": "BLOCKED_UNSET",
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": "BLOCKED_UNSET",
        "formula_denominator": "BLOCKED_UNSET",
        "restatement_carry_law": "BLOCKED_UNSET",
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": "BLOCKED_UNSET",
        "no_bridge_proof": "BLOCKED_UNSET",
    },
    {
        "primitive_id": "ROIC",
        "provider_source_object": "CONCEPTUAL_ONLY",
        "exact_field_identifier": "BLOCKED_UNSET",
        "ciqsec_trading_item_identity": "CIQSEC+trading_item required; unbound",
        "period_perspective_semantics": "BLOCKED_UNSET",
        "pit_availability_timestamp": "BLOCKED_UNSET",
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": "BLOCKED_UNSET",
        "formula_denominator": "BLOCKED_UNSET",
        "restatement_carry_law": "BLOCKED_UNSET",
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": "BLOCKED_UNSET",
        "no_bridge_proof": "BLOCKED_UNSET",
    },
)


@dataclass(frozen=True)
class PrimitiveBind:
    """Exact source bind for one Q primitive."""

    primitive_id: str
    provider_source_object: str
    exact_field_identifier: str
    ciqsec_trading_item_identity: str
    period_perspective_semantics: str
    pit_availability_timestamp: str
    minimum_publication_processing_lag: str
    unit_currency_law: str
    formula_denominator: str
    restatement_carry_law: str
    applicability_rule: str
    missingness_reason: str
    corporate_action_treatment: str
    source_receipt_hash: str
    no_bridge_proof: str

    def unbound_fields(self) -> list[str]:
        missing: list[str] = []
        for name in REQUIRED_PRIMITIVE_FIELDS:
            value = str(getattr(self, name, "")).strip()
            if value.upper() in _BLOCKED_TOKENS or value in _BLOCKED_TOKENS:
                missing.append(name)
            elif "BLOCKED_UNSET" in value.upper() or value.upper().startswith("CONCEPTUAL"):
                missing.append(name)
        return missing

    def is_fully_bound(self) -> bool:
        return not self.unbound_fields()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QSourceContractV1:
    """Machine-readable Q source contract with amendment accounting."""

    contract_id: str = CONTRACT_ID
    slice_id: str = SLICE_ID
    spec_version: str = SPEC_VERSION
    max_outcome_blind_q_amendment_cycles: int = MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES
    q_amendment_cycles_used: int = 0
    primitives: list[PrimitiveBind] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    forbid_silent_synthetic_substitute: bool = True
    forbid_unavailable_field_bridge: bool = True
    forbid_ticker_entity_permno_fallback: bool = True

    def unbound_inventory(self) -> dict[str, list[str]]:
        return {
            p.primitive_id: p.unbound_fields()
            for p in self.primitives
            if not p.is_fully_bound()
        }

    def all_primitives_bound(self) -> bool:
        return bool(self.primitives) and all(p.is_fully_bound() for p in self.primitives)

    def feasibility_verdict(self) -> str:
        """Return one of the four legal S0 feasibility verdicts."""

        if self.q_amendment_cycles_used > self.max_outcome_blind_q_amendment_cycles:
            return Q_SOURCE_BLOCKED
        if not self.primitives:
            return Q_SOURCE_BLOCKED
        if self.all_primitives_bound():
            if self.q_amendment_cycles_used == 0:
                return Q_GF_BOUND
            if self.q_amendment_cycles_used == 1:
                return Q_AMENDED_BOUND
            return Q_SOURCE_BLOCKED
        # Conceptual / incomplete binds: if any primitive is purely conceptual
        # with no exact field, this is blocked rather than a one-shot amendment.
        if any(
            str(p.provider_source_object).upper() in {"CONCEPTUAL_ONLY", "BLOCKED_UNSET"}
            or str(p.exact_field_identifier).upper() in _BLOCKED_TOKENS
            for p in self.primitives
        ):
            return Q_SOURCE_BLOCKED
        if self.q_amendment_cycles_used < self.max_outcome_blind_q_amendment_cycles:
            return Q_MINIMAL_AMENDMENT_REQUIRED
        return Q_SOURCE_BLOCKED

    def record_amendment(self, *, reason: str) -> None:
        """Consume the single allowed outcome-blind amendment cycle."""

        if self.q_amendment_cycles_used >= self.max_outcome_blind_q_amendment_cycles:
            raise ValueError(
                "ok_sbi_0_second_q_redesign_forbidden:new_slice_id_required"
            )
        self.q_amendment_cycles_used += 1
        self.notes.append(f"amendment_cycle_{self.q_amendment_cycles_used}:{reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "slice_id": self.slice_id,
            "spec_version": self.spec_version,
            "max_outcome_blind_q_amendment_cycles": self.max_outcome_blind_q_amendment_cycles,
            "q_amendment_cycles_used": self.q_amendment_cycles_used,
            "primitives": [p.to_dict() for p in self.primitives],
            "unbound_inventory": self.unbound_inventory(),
            "feasibility_verdict": self.feasibility_verdict(),
            "notes": list(self.notes),
            "forbid_silent_synthetic_substitute": self.forbid_silent_synthetic_substitute,
            "forbid_unavailable_field_bridge": self.forbid_unavailable_field_bridge,
            "forbid_ticker_entity_permno_fallback": self.forbid_ticker_entity_permno_fallback,
            "numeric_q_status": (
                "BOUND" if self.all_primitives_bound() else "NOT_BOUND_S0"
            ),
            "outcome_input": False,
            "provider_calls": "FORBIDDEN_THIS_TURN",
        }


def primitive_from_mapping(raw: Mapping[str, Any]) -> PrimitiveBind:
    payload = {name: str(raw.get(name, "BLOCKED_UNSET")) for name in REQUIRED_PRIMITIVE_FIELDS}
    return PrimitiveBind(**payload)


def conceptual_candidate_contract() -> QSourceContractV1:
    """Return the locked conceptual candidate in unbound form (honest S0)."""

    return QSourceContractV1(
        primitives=[primitive_from_mapping(p) for p in CONCEPTUAL_CANDIDATE_PRIMITIVES],
        notes=[
            "RevGrowth_12m+ROIC is conceptual candidate only, not authority.",
            "AO-K0A did not rederive numeric Q; no silent bridge to Rule100 artifacts.",
            "No provider/source substitution authorized this turn.",
        ],
    )


def evaluate_q_source_feasibility(
    contract: QSourceContractV1 | None = None,
) -> dict[str, Any]:
    """Produce the Step-1 feasibility packet."""

    active = contract if contract is not None else conceptual_candidate_contract()
    verdict = active.feasibility_verdict()
    if verdict not in LEGAL_VERDICTS:
        raise AssertionError(f"ok_sbi_0_illegal_q_verdict:{verdict}")
    return {
        "step": 1,
        "step_name": "QSourceContractV1_feasibility",
        "contract": active.to_dict(),
        "Q_feasibility": verdict,
        "q_amendment_cycles_used": active.q_amendment_cycles_used,
        "stop_q_binding": verdict == Q_SOURCE_BLOCKED,
        "invent_q_forbidden": True,
        "second_redesign_requires_new_slice_id": True,
    }


def assert_no_silent_bridge(contract: QSourceContractV1) -> None:
    """Refuse synthetic substitutes and identity fallbacks."""

    for prim in contract.primitives:
        for banned in (
            "TICKER_FALLBACK",
            "PERMNO_FALLBACK",
            "ENTITY_BRIDGE",
            "SYNTHETIC_FILL",
            "RULE100_ARTIFACT_BRIDGE",
            "Z_DEMAND_BRIDGE",
        ):
            blob = " ".join(str(v) for v in prim.to_dict().values()).upper()
            if banned in blob:
                raise ValueError(f"ok_sbi_0_silent_bridge_forbidden:{banned}:{prim.primitive_id}")


def validate_amendment_budget(cycles_used: int) -> None:
    if cycles_used > MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES:
        raise ValueError("ok_sbi_0_second_q_redesign_forbidden:new_slice_id_required")


def required_field_names() -> Sequence[str]:
    return REQUIRED_PRIMITIVE_FIELDS
