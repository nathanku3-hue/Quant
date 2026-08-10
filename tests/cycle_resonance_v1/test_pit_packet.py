from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from research.alpha_pit_v1.contracts import FAMILY_ID, ResearchMode
from research.alpha_pit_v1.fixtures import DeterministicAlphaPITFixtureBackend
from research.alpha_pit_v1.session import open_alpha_pit_session
from research.cycle_resonance_v1.pit_packet import build_cycle_resonance_input_packet


AS_OF = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


def _api():
    return open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="fixture-decision-1",
        backend=DeterministicAlphaPITFixtureBackend(),
    )


def test_crv1_fixture_packet_closes_deterministically_without_outcome_authority() -> None:
    api = _api()
    first = build_cycle_resonance_input_packet(
        api=api,
        implementation_id="CRV1_FIXTURE_IMPL_1",
        decision_context_id="fixture-decision-1",
        as_of=AS_OF,
        coverage_policy_id="CRV1_FIXTURE_COVERAGE_1",
    )
    second = build_cycle_resonance_input_packet(
        api=api,
        implementation_id="CRV1_FIXTURE_IMPL_1",
        decision_context_id="fixture-decision-1",
        as_of=AS_OF,
        coverage_policy_id="CRV1_FIXTURE_COVERAGE_1",
    )
    assert first == second
    assert first["research_mode"] == ResearchMode.CONFIRMATORY.value
    assert first["decision_context_id"] == "fixture-decision-1"
    assert first["authority_class"] == "MECHANICAL_FIXTURE_ZERO_EVIDENCE"
    assert first["financial_alpha_evidence"] == 0
    assert len(first["input_packet_sha256"]) == 64
    assert not hasattr(api, "outcomes")


def test_crv1_package_contains_no_provider_or_discovery_outcome_import() -> None:
    root = Path("research/cycle_resonance_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = ("yfinance", "psycopg2", "CIQCycleV1Adapter", "discovery_outcomes", "permno")
    assert not any(token in text for token in forbidden)
