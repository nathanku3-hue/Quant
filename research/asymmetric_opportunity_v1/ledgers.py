"""OK-SBI-0 four ledgers — never merge, never cross-sell claims."""

from __future__ import annotations

from typing import Any


COMMON_SUPPORT_SCIENTIFIC_LEDGER = "COMMON_SUPPORT_SCIENTIFIC_LEDGER"
APPLICABLE_SYSTEM_LEDGER = "APPLICABLE_SYSTEM_LEDGER"
FULL_W3_OPPORTUNITY_CENSUS = "FULL_W3_OPPORTUNITY_CENSUS"
ABSTENTION_ATTRIBUTION_LEDGER = "ABSTENTION_ATTRIBUTION_LEDGER"

LEDGER_IDS = (
    COMMON_SUPPORT_SCIENTIFIC_LEDGER,
    APPLICABLE_SYSTEM_LEDGER,
    FULL_W3_OPPORTUNITY_CENSUS,
    ABSTENTION_ATTRIBUTION_LEDGER,
)

LEDGER_ROLES = {
    COMMON_SUPPORT_SCIENTIFIC_LEDGER: "conditional novelty / redundancy / synergy only",
    APPLICABLE_SYSTEM_LEDGER: "applicable-domain deployability only",
    FULL_W3_OPPORTUNITY_CENSUS: "full-W3 opportunity + tail census only",
    ABSTENTION_ATTRIBUTION_LEDGER: "foregone right-tail / avoided catastrophe only",
}

# Invalid cross-ledger sales
FORBIDDEN_CLAIM_CROSSWALKS = (
    {
        "from": COMMON_SUPPORT_SCIENTIFIC_LEDGER,
        "sold_as": FULL_W3_OPPORTUNITY_CENSUS,
        "reason": "common-support lift sold as full-W3 deployability",
    },
    {
        "from": FULL_W3_OPPORTUNITY_CENSUS,
        "sold_as": "STRATEGY_PNL",
        "reason": "opportunity census sold as strategy P&L",
    },
    {
        "from": ABSTENTION_ATTRIBUTION_LEDGER,
        "sold_as": "ALPHA",
        "reason": "abstention attribution sold as Alpha",
    },
)


def ledger_catalog() -> dict[str, Any]:
    return {
        "slice_id": "OK-SBI-0",
        "merge_ledgers": "FORBIDDEN",
        "ledgers": [
            {"ledger_id": lid, "role": LEDGER_ROLES[lid]} for lid in LEDGER_IDS
        ],
        "forbidden_claim_crosswalks": list(FORBIDDEN_CLAIM_CROSSWALKS),
    }


def assert_known_ledger(ledger_id: str) -> None:
    if ledger_id not in LEDGER_IDS:
        raise ValueError(f"ok_sbi_0_unknown_ledger:{ledger_id}")


def refuse_ledger_merge(a: str, b: str) -> None:
    raise ValueError(f"ok_sbi_0_ledger_merge_forbidden:{a}+{b}")
