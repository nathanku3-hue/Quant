"""OK-SBI-0 numeric / hash release blockers and machine freeze law."""

from __future__ import annotations

from typing import Any, Mapping


BLOCKED_TOKENS = frozenset(
    {
        "BLOCKED_UNSET",
        "TBD",
        "NULL",
        "PLACEHOLDER",
        "UNHASHED",
        "UNLANDED",
        "",
        "NONE",
    }
)

# Must bind real values (not prose) before S0→S1.
NUMERIC_GATE_FIELDS = (
    "K_t_schedule",
    "right_tail_definition_Q_CLOCK",
    "right_tail_definition_M_CLOCK",
    "catastrophe_definition_Q_CLOCK",
    "catastrophe_definition_M_CLOCK",
    "execution_lag",
    "cost_law",
    "delta_economic",
    "epsilon_catastrophe",
    "coverage_tolerances",
    "confidence_level",
    "temporal_block_definition",
    "stability_rule",
    "multiple_testing_method",
    "minimum_effective_episodes",
    "random_seed_repetition_law",
    "code_hash",
    "source_hash",
    "contract_hash",
    "denominator_hash",
    "Q_CLOCK_LABEL_PACK_sha256",
    "M_CLOCK_LABEL_PACK_sha256",
    "q_source_binding_hash",
)


def default_blocked_gates() -> dict[str, str]:
    return {name: "BLOCKED_UNSET" for name in NUMERIC_GATE_FIELDS}


def is_blocked_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.upper() in BLOCKED_TOKENS or text in BLOCKED_TOKENS


def inventory_blockers(gates: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    for name in NUMERIC_GATE_FIELDS:
        if name not in gates or is_blocked_value(gates.get(name)):
            blocked.append(name)
        else:
            # also catch embedded blocked tokens
            text = str(gates[name])
            if "BLOCKED_UNSET" in text.upper():
                blocked.append(name)
    # any extra fields that are still blocked tokens
    for name, value in gates.items():
        if name not in NUMERIC_GATE_FIELDS and is_blocked_value(value):
            blocked.append(name)
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for name in blocked:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def machine_law(gates: Mapping[str, Any]) -> dict[str, Any]:
    blocked = inventory_blockers(gates)
    count = len(blocked)
    runnable = count == 0
    return {
        "STATE": (
            "S1_PREOPEN_READY_AWAITING_STOPLINE_CARVEOUT"
            if runnable
            else "S0_DESIGN_LOCKED_RELEASE_BLOCKED"
        ),
        "runnable_evaluation": runnable,
        "blocked_field_count": count,
        "blocked_fields": blocked,
        "outcome_open_authorized": False,
        "release_now": False,
        "law": "runnable_evaluation = (blocked_field_count == 0)",
        "do_not_invent_owner_unapproved_numbers": True,
    }


def review_bar() -> dict[str, Any]:
    return {
        "S0_to_S1": (
            "mechanical pre-open PASS + all hashes replay + PRODUCT_PREOPEN PASS "
            "+ blockers zero"
        ),
        "S1_to_S2": "owner/CRO signed carve-out OK-SBI-0-DEV-OPEN-1; SAW may be UNAVAILABLE",
        "S2_to_S3_RESEARCH_ONLY": (
            "deterministic result receipt + PRODUCT_RESULT PASS; "
            "SAW_UNAVAILABLE recorded as coverage-limited"
        ),
        "S3_to_S4_CANDIDATE": "full SAW A/B/C or owner-approved triple independent reviews",
        "SAW_UNAVAILABLE_is_research_scientific_failure": False,
        "SAW_UNAVAILABLE_is_candidate_promotion_blocker": True,
    }


def refuse_outcome_open(*, blocked_field_count: int) -> None:
    if blocked_field_count != 0:
        raise ValueError(
            "ok_sbi_0_outcome_open_forbidden:"
            f"blocked_field_count={blocked_field_count}"
        )
    raise ValueError(
        "ok_sbi_0_outcome_open_forbidden:missing_OK-SBI-0-DEV-OPEN-1_carveout"
    )
