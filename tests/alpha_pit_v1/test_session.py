from __future__ import annotations

from datetime import UTC, datetime
import sys

import pytest

from research.alpha_pit_v1.contracts import (
    CRV1_FAMILY_DATA_CONTRACT,
    CRV1_PRIMARY_LABEL_SPEC_ID,
    FAMILY_ID,
    VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT,
    ResearchMode,
)
from research.alpha_pit_v1.fixtures import DeterministicAlphaPITFixtureBackend
from research.alpha_pit_v1.session import open_alpha_pit_session


AS_OF = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


def _open(mode: ResearchMode):
    return open_alpha_pit_session(
        mode=mode,
        family_id=FAMILY_ID,
        decision_context_id="fixture-decision-1",
        backend=DeterministicAlphaPITFixtureBackend(),
    )


def test_confirmatory_capability_has_no_outcomes_and_does_not_load_discovery_module() -> None:
    sys.modules.pop("research.alpha_pit_v1.discovery_outcomes", None)
    api = _open(ResearchMode.CONFIRMATORY)
    assert not hasattr(api, "outcomes")
    assert "research.alpha_pit_v1.discovery_outcomes" not in sys.modules


def test_prospective_capability_has_no_outcomes() -> None:
    api = _open(ResearchMode.PROSPECTIVE)
    assert not hasattr(api, "outcomes")


def test_discovery_capability_exposes_fixture_outcomes_with_zero_authority() -> None:
    api = _open(ResearchMode.DISCOVERY)
    risk_set = api.risk_set(as_of=AS_OF)
    outcome = api.outcomes(risk_set_id=risk_set.payload["risk_set_id"])
    assert outcome.manifest["authority_class"] == "MECHANICAL_FIXTURE_ZERO_EVIDENCE"
    assert outcome.manifest["financial_alpha_evidence"] == 0
    assert outcome.payload["denominator_count"] == 2


def test_discovery_outcome_label_is_bound_to_the_active_family_contract() -> None:
    api = _open(ResearchMode.DISCOVERY)
    risk_set = api.risk_set(as_of=AS_OF)
    with pytest.raises(ValueError, match="outcome_label_spec_invalid"):
        api.outcomes(
            risk_set_id=risk_set.payload["risk_set_id"],
            label_spec_id=VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT.primary_label_spec_id,
        )


def test_same_fixture_request_is_content_addressed_deterministically() -> None:
    api = _open(ResearchMode.CONFIRMATORY)
    first = api.observations(ids=["CIQSEC:101"], fields=["market.close"], as_of=AS_OF)
    second = api.observations(ids=["CIQSEC:101"], fields=["market.close"], as_of=AS_OF)
    assert first.payload_sha256 == second.payload_sha256
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.manifest["created_at"] == "2026-01-01T00:00:01.000000Z"


def test_payload_hash_tamper_fails_closed_at_read_boundary() -> None:
    class TamperedFixtureBackend(DeterministicAlphaPITFixtureBackend):
        def risk_set(self, *, as_of, research_mode):
            ref = super().risk_set(as_of=as_of, research_mode=research_mode)
            ref.payload["rows"][0]["eligibility_status"] = "TAMPERED_AFTER_HASH"
            return ref

    api = open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="fixture-decision-1",
        backend=TamperedFixtureBackend(),
    )
    with pytest.raises(ValueError, match="payload_hash_mismatch"):
        api.risk_set(as_of=AS_OF)


def test_available_at_after_as_of_fails_closed() -> None:
    api = _open(ResearchMode.CONFIRMATORY)
    with pytest.raises(ValueError, match="available_at_after_as_of"):
        api.risk_set(as_of=datetime(2025, 12, 31, 20, 30, tzinfo=UTC))


def test_ticker_identity_and_unknown_field_fail_closed() -> None:
    api = _open(ResearchMode.CONFIRMATORY)
    with pytest.raises(ValueError, match="ciq_security_id_namespace_required"):
        api.observations(ids=["AAPL"], fields=["market.close"], as_of=AS_OF)
    with pytest.raises(ValueError, match="unknown_observation_field"):
        api.observations(ids=["CIQSEC:101"], fields=["future.magic"], as_of=AS_OF)


def test_family_two_contract_is_narrow_and_cross_family_artifacts_fail_closed() -> None:
    contract = VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT
    assert set(contract.as_dict()) == {
        "family_id",
        "risk_set_spec_id",
        "primary_label_spec_id",
        "allowed_observation_surface",
        "allowed_expectation_surface",
        "allowed_claim_surface",
    }
    assert contract.allowed_observation_surface == (
        "market.close",
        "market.total_return_1d",
        "market.volume",
    )
    assert contract.allowed_expectation_surface == ()
    assert contract.allowed_claim_surface == ()

    api = open_alpha_pit_session(
        mode=ResearchMode.PROSPECTIVE,
        family_id=contract.family_id,
        decision_context_id="vsb-prospective-1",
        backend=DeterministicAlphaPITFixtureBackend(),
        family_contract=contract,
    )
    assert api.family_contract == contract
    assert not hasattr(api, "outcomes")
    with pytest.raises(ValueError, match="observation_surface_forbidden"):
        api.observations(ids=["CIQSEC:101"], fields=["fund.revenue_q"], as_of=AS_OF)
    with pytest.raises(ValueError, match="claim_surface_forbidden"):
        api.source_claims(ids=["CIQSEC:101"], as_of=AS_OF)
    with pytest.raises(ValueError, match="expectation_surface_forbidden"):
        api.expectations(ids=["CIQSEC:101"], as_of=AS_OF)
    with pytest.raises(ValueError, match="manifest_contract_invalid"):
        api.risk_set(as_of=AS_OF)


def test_family_two_discovery_outcomes_bind_only_the_family_label() -> None:
    contract = VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT
    backend = DeterministicAlphaPITFixtureBackend(family_contract=contract)
    api = open_alpha_pit_session(
        mode=ResearchMode.DISCOVERY,
        family_id=contract.family_id,
        decision_context_id="vsb-discovery-1",
        backend=backend,
        family_contract=contract,
    )
    risk_set = api.risk_set(as_of=AS_OF)
    outcome = api.outcomes(risk_set_id=risk_set.payload["risk_set_id"])
    assert outcome.payload["family_id"] == contract.family_id
    assert outcome.payload["label_spec_id"] == contract.primary_label_spec_id
    with pytest.raises(ValueError, match="outcome_label_spec_invalid"):
        api.outcomes(
            risk_set_id=risk_set.payload["risk_set_id"],
            label_spec_id=CRV1_PRIMARY_LABEL_SPEC_ID,
        )


def test_parallel_family_session_state_is_isolated() -> None:
    crv1 = open_alpha_pit_session(
        mode=ResearchMode.PROSPECTIVE,
        family_id=FAMILY_ID,
        decision_context_id="crv1-prospective-1",
        backend=DeterministicAlphaPITFixtureBackend(),
        family_contract=CRV1_FAMILY_DATA_CONTRACT,
    )
    vsb = open_alpha_pit_session(
        mode=ResearchMode.PROSPECTIVE,
        family_id=VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT.family_id,
        decision_context_id="vsb-prospective-1",
        backend=DeterministicAlphaPITFixtureBackend(),
        family_contract=VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT,
    )
    assert crv1.family_id == "CYCLE_RESONANCE_v1"
    assert vsb.family_id == "VOL_SQUEEZE_BREAKOUT_v1"
    assert crv1.family_contract != vsb.family_contract
    assert crv1.decision_context_id != vsb.decision_context_id
