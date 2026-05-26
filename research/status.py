"""Closed vocabulary for research evidence status."""

from __future__ import annotations

from enum import StrEnum


class ResearchStatus(StrEnum):
    """Mechanical status values for research evidence gates."""

    DIAGNOSTIC_ONLY = "diagnostic_only"
    EXPLORATORY = "exploratory"
    RESEARCH_VALID = "research_valid"
    CANDIDATE_READY = "candidate_ready"
    BLOCKED = "blocked"


_STATUS_VALUES = frozenset(status.value for status in ResearchStatus)


def validate_research_status(value: str | ResearchStatus) -> ResearchStatus:
    """Return a status enum or raise for values outside the closed vocabulary."""

    if isinstance(value, ResearchStatus):
        return value
    try:
        return ResearchStatus(str(value))
    except ValueError as exc:
        allowed = ", ".join(sorted(_STATUS_VALUES))
        raise ValueError(f"Unknown research status {value!r}; allowed: {allowed}") from exc


def research_status_values() -> tuple[str, ...]:
    """Return stable status values for schema checks."""

    return tuple(status.value for status in ResearchStatus)
