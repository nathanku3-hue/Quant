"""Fail-closed preflight for recurring AOV-0 frozen-109 weekly cuts.

This module does not acquire provider data, build a decision cut, create a seal,
or open outcomes.  It only proves that a prospective weekly attempt is using the
same frozen candidate laboratory and newly retrieved required source domains.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import assert_sha256, domain_hash


WEEKLY_TAPE_PREFLIGHT_SCHEMA = "aov0_weekly_tape_preflight_v1"
FROZEN_CANDIDATE_COUNT = 109
CLOCK1_FROZEN_CANDIDATE_UNIVERSE_SHA256 = "f4f7ac7ed1ff21b95580bb623953e875bda0106ed478887b7d5ed6ccff456075"
CLOCK1_FROZEN_CANDIDATE_SOURCE_SHA256 = "17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056"
CLOCK1_FROZEN_CANDIDATE_ENTITY_IDS = (
    "10088110",
    "101214465",
    "10461017",
    "106003939",
    "10656431",
    "106603589",
    "106972853",
    "107021323",
    "107089758",
    "108126092",
    "10844958",
    "109828157",
    "110336920",
    "113050522",
    "113253016",
    "113495488",
    "117876626",
    "118388161",
    "118388356",
    "118428555",
    "11916855",
    "123916273",
    "13087393",
    "131002399",
    "131468609",
    "13373011",
    "133988500",
    "14338380",
    "14399568",
    "14887727",
    "19095891",
    "19098526",
    "20304639",
    "20676534",
    "25812177",
    "26009198",
    "26518656",
    "27859111",
    "28192562",
    "28743844",
    "28846952",
    "29188222",
    "29521085",
    "29657689",
    "4094286",
    "4096690",
    "4142027",
    "4160258",
    "4199629",
    "4205752",
    "4209142",
    "4238544",
    "4276821",
    "4282769",
    "4287903",
    "4304239",
    "4318095",
    "4352761",
    "4356306",
    "4424169",
    "4580570",
    "4810358",
    "4810724",
    "4810824",
    "4810896",
    "4811105",
    "4811117",
    "4811532",
    "4811624",
    "4811760",
    "4865862",
    "4898489",
    "4913803",
    "4913901",
    "4913905",
    "4972261",
    "4972296",
    "4988279",
    "4989077",
    "4991374",
    "4992232",
    "4995890",
    "4996395",
    "5000790",
    "5013726",
    "5109836",
    "5214991",
    "5231291",
    "5242080",
    "5255493",
    "5265242",
    "5267913",
    "5298533",
    "5302933",
    "5303886",
    "5316615",
    "5990414",
    "6319660",
    "6459368",
    "6544540",
    "6910410",
    "6963342",
    "7001816",
    "7727865",
    "8241746",
    "9098887",
    "9176842",
    "9370215",
    "9768877",
)
REQUIRED_SOURCE_IDS = {
    "ciq_quarterly_fundamentals": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
    "ciq_security_master": "SPCIQPRO:PRIMARY_SECURITY_MASTER",
    "ciq_market_data": "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
    "nyfed_sofr": "NYFED:SOFR",
}


def _utc(value: str | datetime, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"aov0_weekly_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"aov0_weekly_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _candidate_ids(values: Sequence[object], *, field: str) -> tuple[str, ...]:
    ids = tuple(sorted(str(value).strip() for value in values))
    if len(ids) != FROZEN_CANDIDATE_COUNT:
        raise ValueError(f"aov0_weekly_{field}_count_must_equal_109")
    if any(not value for value in ids):
        raise ValueError(f"aov0_weekly_{field}_blank_id")
    if len(set(ids)) != FROZEN_CANDIDATE_COUNT:
        raise ValueError(f"aov0_weekly_{field}_duplicate_id")
    return ids


def frozen_candidate_universe_hash(candidate_entity_ids: Sequence[object]) -> str:
    ids = _candidate_ids(candidate_entity_ids, field="frozen_candidate_universe")
    return domain_hash(
        "AOV0:FROZEN_109_CANDIDATE_UNIVERSE:V1",
        {"candidate_count": FROZEN_CANDIDATE_COUNT, "candidate_entity_ids": list(ids)},
    )


def _bind_receipt(
    *,
    name: str,
    receipt: Mapping[str, Any],
    previous_cut_at: datetime,
    current_cut_at: datetime,
) -> dict[str, str]:
    expected_source = REQUIRED_SOURCE_IDS[name]
    source_id = str(receipt.get("source_id") or "")
    if source_id != expected_source:
        raise ValueError(f"aov0_weekly_source_id_mismatch:{name}")
    raw_hash = str(receipt.get("raw_object_sha256") or "")
    try:
        assert_sha256(raw_hash)
    except ValueError as exc:
        raise ValueError(f"aov0_weekly_raw_hash_invalid:{name}") from exc
    retrieved = _utc(receipt.get("retrieved_at"), field=f"retrieved_at_{name}")
    if retrieved <= previous_cut_at:
        raise ValueError(f"aov0_weekly_stale_required_source:{name}")
    if retrieved > current_cut_at:
        raise ValueError(f"aov0_weekly_future_retrieval:{name}")
    return {
        "source_id": source_id,
        "retrieved_at": _utc_text(retrieved),
        "raw_object_sha256": raw_hash,
    }


def build_weekly_tape_preflight(
    *,
    frozen_candidate_entity_ids: Sequence[object],
    refreshed_candidate_entity_ids: Sequence[object],
    previous_cut_at: str | datetime,
    current_cut_at: str | datetime,
    source_receipts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate one prospective weekly attempt before decision-cut construction.

    Freshness is intentionally strict: every required source receipt must have a
    retrieval timestamp strictly after the prior cut.  This prevents silent reuse
    of last week's required state while avoiding invented field-specific max-age
    constants.
    """

    previous = _utc(previous_cut_at, field="previous_cut_at")
    current = _utc(current_cut_at, field="current_cut_at")
    if current <= previous:
        raise ValueError("aov0_weekly_cut_order_invalid")

    frozen = _candidate_ids(frozen_candidate_entity_ids, field="frozen_candidate_universe")
    refreshed = _candidate_ids(refreshed_candidate_entity_ids, field="refreshed_candidate_universe")
    expected = tuple(sorted(CLOCK1_FROZEN_CANDIDATE_ENTITY_IDS))
    if frozen != expected:
        raise ValueError("aov0_weekly_frozen_candidate_universe_not_clock1")
    if refreshed != frozen:
        raise ValueError("aov0_weekly_frozen_candidate_membership_drift")

    if set(source_receipts) != set(REQUIRED_SOURCE_IDS):
        missing = sorted(set(REQUIRED_SOURCE_IDS) - set(source_receipts))
        extra = sorted(set(source_receipts) - set(REQUIRED_SOURCE_IDS))
        raise ValueError(
            "aov0_weekly_required_source_set_invalid:"
            f"missing={','.join(missing)};extra={','.join(extra)}"
        )

    fundamentals = source_receipts["ciq_quarterly_fundamentals"]
    if int(fundamentals.get("company_universe_entity_count", -1)) != FROZEN_CANDIDATE_COUNT:
        raise ValueError("aov0_weekly_fundamentals_frozen_entity_count_invalid")
    for name in ("ciq_security_master", "ciq_market_data"):
        if int(source_receipts[name].get("frozen_entity_count", -1)) != FROZEN_CANDIDATE_COUNT:
            raise ValueError(f"aov0_weekly_frozen_entity_count_invalid:{name}")

    bindings = {
        name: _bind_receipt(
            name=name,
            receipt=source_receipts[name],
            previous_cut_at=previous,
            current_cut_at=current,
        )
        for name in sorted(REQUIRED_SOURCE_IDS)
    }
    universe_hash = frozen_candidate_universe_hash(frozen)
    if universe_hash != CLOCK1_FROZEN_CANDIDATE_UNIVERSE_SHA256:
        raise RuntimeError("aov0_weekly_clock1_candidate_hash_constant_invalid")
    body = {
        "schema_version": WEEKLY_TAPE_PREFLIGHT_SCHEMA,
        "candidate_count": FROZEN_CANDIDATE_COUNT,
        "candidate_universe_sha256": universe_hash,
        "candidate_source_sha256": CLOCK1_FROZEN_CANDIDATE_SOURCE_SHA256,
        "previous_cut_at": _utc_text(previous),
        "current_cut_at": _utc_text(current),
        "source_receipts": bindings,
        "growth_screen_rerun_authorized": False,
        "parent_child_mutation_authority": "NONE",
        "outcome_open_authority": "NONE",
        "financial_alpha_evidence": 0,
        "status": "READY_FOR_V3_DECISION_CUT_CONSTRUCTION",
    }
    return {
        **body,
        "preflight_id": domain_hash("AOV0:WEEKLY_TAPE_PREFLIGHT:V1", body),
    }
