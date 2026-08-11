from __future__ import annotations

import pytest

from research.asymmetric_opportunity_v1.claim_schema import (
    ClaimReceiptV1,
    empty_claim_template,
    refuse_untagged_sentence,
    schema_document,
    validate_claim,
)
from research.asymmetric_opportunity_v1.ledgers import (
    ABSTENTION_ATTRIBUTION_LEDGER,
    COMMON_SUPPORT_SCIENTIFIC_LEDGER,
    FULL_W3_OPPORTUNITY_CENSUS,
    refuse_ledger_merge,
)


def _valid_claim(**overrides):
    base = empty_claim_template()
    base.update(
        {
            "claim_id": "c1",
            "slice_id": "OK-SBI-0",
            "evaluation_job_id": "job1",
            "result_receipt_sha256": "b" * 64,
            "ledger_id": COMMON_SUPPORT_SCIENTIFIC_LEDGER,
            "clock_id": "Q_CLOCK",
            "arm_id": "A1_Q_NATIVE",
            "comparator_arm_id": "A2_M_RAW",
            "metric_id": "right_tail_enrichment",
            "population_scope": "Q_AND_M_OBSERVED",
            "population_sha256": "c" * 64,
            "applicability_scope": "APPLICABLE_OBSERVED",
            "status_stratum": "ELIGIBLE_COMPLETE",
            "K_schedule_id": "K_TBD",
            "label_pack_sha256": "d" * 64,
            "numerator": "1",
            "denominator": "10",
            "estimate": "0.1",
            "uncertainty_method": "block_bootstrap",
            "confidence_interval": "[0,1]",
            "claim_authority": "RESEARCH_ONLY",
        }
    )
    base.update(overrides)
    return base


def test_schema_requires_ledger_and_clock() -> None:
    doc = schema_document()
    assert "ledger_id" in doc["required_fields"]
    assert "clock_id" in doc["required_fields"]
    assert doc["untagged_claim"] == "INVALID"


def test_valid_claim_passes() -> None:
    result = validate_claim(_valid_claim())
    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_ledger_or_clock_invalid() -> None:
    r1 = validate_claim(_valid_claim(ledger_id="BLOCKED_UNSET"))
    assert r1["valid"] is False
    assert any("ledger" in e for e in r1["errors"])
    r2 = validate_claim(_valid_claim(clock_id=""))
    assert r2["valid"] is False
    assert any("clock" in e for e in r2["errors"])


def test_crosswalk_refusals() -> None:
    r = validate_claim(
        _valid_claim(
            ledger_id=COMMON_SUPPORT_SCIENTIFIC_LEDGER,
            sold_as="FULL_W3_DEPLOYABILITY",
        )
    )
    assert r["valid"] is False
    assert "common_support_sold_as_full_w3_deployability" in r["errors"]

    r2 = validate_claim(
        _valid_claim(
            ledger_id=FULL_W3_OPPORTUNITY_CENSUS,
            sold_as="STRATEGY_PNL",
        )
    )
    assert "opportunity_census_sold_as_strategy_pnl" in r2["errors"]

    r3 = validate_claim(
        _valid_claim(
            ledger_id=ABSTENTION_ATTRIBUTION_LEDGER,
            sold_as="ALPHA",
        )
    )
    assert "abstention_sold_as_alpha" in r3["errors"]


def test_refuse_untagged_and_ledger_merge() -> None:
    with pytest.raises(ValueError, match="untagged_claim"):
        refuse_untagged_sentence(ledger_id=None, clock_id="Q_CLOCK")
    with pytest.raises(ValueError, match="ledger_merge_forbidden"):
        refuse_ledger_merge(COMMON_SUPPORT_SCIENTIFIC_LEDGER, FULL_W3_OPPORTUNITY_CENSUS)


def test_dataclass_roundtrip() -> None:
    raw = _valid_claim()
    claim = ClaimReceiptV1(**{k: raw[k] for k in ClaimReceiptV1.__dataclass_fields__})
    assert validate_claim(claim)["valid"] is True
