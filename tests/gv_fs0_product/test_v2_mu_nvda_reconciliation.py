"""Tests for bounded MU/NVDA G_supply reconciliation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.gv_v2_mu_nvda_reconciliation import (
    CONTRADICTION_NONE,
    CORROBORATION_PARTIAL,
    DISPOSITION_HOLD,
    PORTFOLIO_ACTION_NO_POSITION,
    RESEARCH_ACTION_HOLD,
    MuNvdaReconciliationError,
    build_mu_nvda_reconciliation,
    load_verified_mu_nvda_reconciliation,
    run_mu_nvda_reconciliation,
)

ROOT = Path(__file__).resolve().parents[2]
MU = ROOT / "data" / "gv_v2_b0b" / "mu_0000723125-26-000015"
NVDA = (
    ROOT
    / "data"
    / "gv_v2_alpha0"
    / "family_two_nvda_0001045810-26-000052"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _build() -> dict[str, object]:
    return build_mu_nvda_reconciliation(
        mu_claim=_load(MU / "claim_evaluation.json"),
        mu_research=_load(MU / "research_decision.json"),
        nvda_fact_set=_load(NVDA / "fact_set.json"),
        nvda_research=_load(NVDA / "research_decision.json"),
    )


def test_reconciliation_holds_without_alpha_or_portfolio_mutation() -> None:
    result = _build()
    assert result["corroboration_status"] == CORROBORATION_PARTIAL
    assert result["contradiction_status"] == CONTRADICTION_NONE
    assert result["disposition"] == DISPOSITION_HOLD
    assert result["research_action"] == RESEARCH_ACTION_HOLD
    assert result["portfolio_action"] == PORTFOLIO_ACTION_NO_POSITION
    assert result["independent_source_family_count"] == 2
    assert result["alpha_claim"] is False
    assert result["investability_claim"] is False
    assert result["portfolio_mutation_authorized"] is False
    assert "Micron-specific physical supply" in result["missing_discriminator"]
    assert len(result["corroboration"]) == 2
    assert result["contradictions"] == []
    lowered = json.dumps(result, sort_keys=True).lower()
    assert '"score"' not in lowered
    assert '"rank"' not in lowered


def test_reconciliation_is_deterministic_and_bound_to_source_hashes() -> None:
    first = _build()
    second = _build()
    assert first == second
    assert first["reconciliation_hash"] == second["reconciliation_hash"]
    bindings = first["source_bindings"]
    assert bindings["mu_claim_evaluation_hash"]
    assert bindings["mu_research_decision_hash"]
    assert bindings["nvda_fact_set_hash"]
    assert bindings["nvda_research_decision_hash"]


def test_tampered_nvda_fact_set_fails_closed() -> None:
    fact_set = _load(NVDA / "fact_set.json")
    tampered = deepcopy(fact_set)
    tampered["facts"][0]["exact_excerpt"] = "fabricated"
    with pytest.raises(MuNvdaReconciliationError, match="NVDA_FACT_SET_HASH_MISMATCH"):
        build_mu_nvda_reconciliation(
            mu_claim=_load(MU / "claim_evaluation.json"),
            mu_research=_load(MU / "research_decision.json"),
            nvda_fact_set=tampered,
            nvda_research=_load(NVDA / "research_decision.json"),
        )


def test_run_writes_bounded_result_and_packet(tmp_path: Path) -> None:
    output = tmp_path / "reconciliation"
    result = run_mu_nvda_reconciliation(output_dir=output)
    result_path = output / "reconciliation_result.json"
    stored = _load(result_path)
    assert stored == result
    assert load_verified_mu_nvda_reconciliation(result_path=result_path) == result
    packet = (output / "decision_packet.md").read_text(encoding="utf-8")
    assert "HOLD_FOR_EVIDENCE" in packet
    assert "NO_POSITION" in packet
    assert "Missing discriminator" in packet
    assert "No score, rank, alpha" in packet


def test_verified_loader_rejects_persisted_result_drift(tmp_path: Path) -> None:
    output = tmp_path / "reconciliation"
    run_mu_nvda_reconciliation(output_dir=output)
    result_path = output / "reconciliation_result.json"
    tampered = _load(result_path)
    tampered["rationale"] = "manufactured positive conclusion"
    result_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(
        MuNvdaReconciliationError, match="RECONCILIATION_RESULT_MISMATCH"
    ):
        load_verified_mu_nvda_reconciliation(result_path=result_path)
