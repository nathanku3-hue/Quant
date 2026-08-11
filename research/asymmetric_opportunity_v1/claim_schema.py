"""OK-SBI-0 ledger-tagged claim schema — every future numeric claim must bind tags."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping

from research.asymmetric_opportunity_v1.ledgers import (
    FORBIDDEN_CLAIM_CROSSWALKS,
    LEDGER_IDS,
    assert_known_ledger,
)

CLAIM_SCHEMA_ID = "OkSbi0ClaimReceiptSchemaV1"
SPEC_VERSION = "v1.2"

CLOCK_Q = "Q_CLOCK"
CLOCK_M = "M_CLOCK"
CLOCK_IDS = frozenset({CLOCK_Q, CLOCK_M, "CAPITAL_TIME_REPORT_ONLY"})

REQUIRED_CLAIM_FIELDS = (
    "claim_id",
    "slice_id",
    "evaluation_job_id",
    "result_receipt_sha256",
    "ledger_id",
    "clock_id",
    "arm_id",
    "comparator_arm_id",
    "metric_id",
    "population_scope",
    "population_sha256",
    "applicability_scope",
    "status_stratum",
    "K_schedule_id",
    "label_pack_sha256",
    "numerator",
    "denominator",
    "estimate",
    "uncertainty_method",
    "confidence_interval",
    "claim_authority",
)

_BLOCKED = frozenset(
    {"", "BLOCKED_UNSET", "TBD", "NULL", "PLACEHOLDER", "UNHASHED", "UNLANDED", "NONE"}
)


@dataclass
class ClaimReceiptV1:
    claim_id: str
    slice_id: str
    evaluation_job_id: str
    result_receipt_sha256: str
    ledger_id: str
    clock_id: str
    arm_id: str
    comparator_arm_id: str
    metric_id: str
    population_scope: str
    population_sha256: str
    applicability_scope: str
    status_stratum: str
    K_schedule_id: str
    label_pack_sha256: str
    numerator: str
    denominator: str
    estimate: str
    uncertainty_method: str
    confidence_interval: str
    claim_authority: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def schema_document() -> dict[str, Any]:
    return {
        "schema_id": CLAIM_SCHEMA_ID,
        "spec_version": SPEC_VERSION,
        "slice_id": "OK-SBI-0",
        "required_fields": list(REQUIRED_CLAIM_FIELDS),
        "legal_ledger_ids": list(LEDGER_IDS),
        "legal_clock_ids": sorted(CLOCK_IDS),
        "invalid_by_construction": [
            "common-support lift sold as full-W3 deployability",
            "opportunity census sold as strategy P&L",
            "abstention attribution sold as Alpha",
            "any result sentence without ledger_id or clock_id",
        ],
        "forbidden_claim_crosswalks": list(FORBIDDEN_CLAIM_CROSSWALKS),
        "untagged_claim": "INVALID",
        "outcome_open_required_for_numeric_result": True,
        "s0_numeric_result_claims": "FORBIDDEN",
    }


def _is_blocked(value: Any) -> bool:
    text = str(value).strip()
    return text.upper() in _BLOCKED or text in _BLOCKED


def validate_claim(claim: Mapping[str, Any] | ClaimReceiptV1) -> dict[str, Any]:
    """Validate claim tags.  Missing ledger_id / clock_id is invalid by construction."""

    raw = claim.to_dict() if isinstance(claim, ClaimReceiptV1) else dict(claim)
    errors: list[str] = []

    for name in REQUIRED_CLAIM_FIELDS:
        if name not in raw or _is_blocked(raw.get(name)):
            errors.append(f"missing_or_blocked:{name}")

    ledger = str(raw.get("ledger_id", ""))
    clock = str(raw.get("clock_id", ""))
    if not ledger or _is_blocked(ledger):
        errors.append("untagged_missing_ledger_id")
    else:
        try:
            assert_known_ledger(ledger)
        except ValueError as exc:
            errors.append(str(exc))

    if not clock or _is_blocked(clock):
        errors.append("untagged_missing_clock_id")
    elif clock not in CLOCK_IDS:
        errors.append(f"unknown_clock_id:{clock}")

    # Explicit crosswalk refusals
    sold_as = str(raw.get("sold_as", "")).upper()
    if ledger == "COMMON_SUPPORT_SCIENTIFIC_LEDGER" and sold_as in {
        "FULL_W3_DEPLOYABILITY",
        "FULL_W3_OPPORTUNITY_CENSUS",
    }:
        errors.append("common_support_sold_as_full_w3_deployability")
    if ledger == "FULL_W3_OPPORTUNITY_CENSUS" and sold_as in {"STRATEGY_PNL", "PNL", "ALPHA"}:
        errors.append("opportunity_census_sold_as_strategy_pnl")
    if ledger == "ABSTENTION_ATTRIBUTION_LEDGER" and sold_as in {"ALPHA", "FINANCIAL_ALPHA"}:
        errors.append("abstention_sold_as_alpha")

    valid = not errors
    return {
        "valid": valid,
        "errors": errors,
        "schema_id": CLAIM_SCHEMA_ID,
        "claim_id": raw.get("claim_id"),
    }


def refuse_untagged_sentence(*, ledger_id: str | None, clock_id: str | None) -> None:
    if not ledger_id or not clock_id:
        raise ValueError("ok_sbi_0_untagged_claim_forbidden:missing_ledger_or_clock")


def claim_field_names() -> tuple[str, ...]:
    return REQUIRED_CLAIM_FIELDS


def empty_claim_template() -> dict[str, str]:
    return {name: "BLOCKED_UNSET" for name in REQUIRED_CLAIM_FIELDS}
