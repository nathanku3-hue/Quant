from __future__ import annotations

import pytest

from research.status import ResearchStatus, research_status_values, validate_research_status


def test_research_status_vocab_is_closed() -> None:
    assert research_status_values() == (
        "diagnostic_only",
        "exploratory",
        "research_valid",
        "candidate_ready",
        "blocked",
    )
    assert validate_research_status("research_valid") == ResearchStatus.RESEARCH_VALID

    with pytest.raises(ValueError, match="Unknown research status"):
        validate_research_status("paper_alpha")
