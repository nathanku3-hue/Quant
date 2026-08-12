"""Fail-closed admission of independent broad CIQ custody for CRV1.

This module performs no provider or network acquisition.  It accepts two
already-landed, hash-receipted CRV1 capture artifacts:

* a broad U.S. primary-common identity snapshot; and
* matching primary-security daily market history.

It derives the frozen ``CRV1_US_PRIMARY_COMMON_V1`` risk-set source and the
structured identity/market receipts consumed by :class:`CiqCycleV1Adapter`.
The AOV growth-screen 109 is not an admissible input authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from research.alpha_pit_v1.adapters.ciq_cycle_v1 import (
    CIQ_PROVIDER,
    CIQ_RISK_SET_SOURCE_ID,
    CRV1_IDENTITY_RECEIPT_SCHEMA,
    CRV1_MARKET_RECEIPT_SCHEMA,
    CRV1_STRUCTURED_SOURCE_SCOPE,
    FAMILY_ID,
    IDENTITY_SOURCE_ID,
    MARKET_SOURCE_ID,
    RISK_SET_ELIGIBILITY_CONTRACT,
    RISK_SET_ELIGIBILITY_CONTRACT_ID,
    RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
    RISK_SET_RECEIPT_SCHEMA,
    RISK_SET_SOURCE_SCHEMA,
    RISK_SET_SPEC_ID,
)
from research.aov0.contracts import normalize_security_id


IDENTITY_CAPTURE_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_primary_security_master_capture_receipt_v1"
MARKET_CAPTURE_RECEIPT_SCHEMA = "alpha_pit_ciq_crv1_primary_security_market_capture_receipt_v1"
CAPTURE_SCOPE = "CRV1_US_PRIMARY_COMMON_NON_GROWTH_CAPTURE_V1"

IDENTITY_COLUMNS = {
    "SP_ENTITY_ID",
    "SP_CIQ_ID",
    "SPT_INSTRUMENT_ITEM_ID",
    "Exchange",
    "Description",
    "Status",
    "PRIMARY_LISTING_ID",
    "LISTING_COUNTRY",
    "PRIMARY_LISTING",
    "SECURITY_CLASS",
    "TRADING_STATUS",
    "IDENTITY_STATUS",
}
MARKET_COLUMNS = {
    "SPT_DATE",
    "SP_CIQ_ID",
    "SPT_INSTRUMENT_ITEM_ID",
    "SP_TOTAL_RETURN",
    "SP_PRICE_CLOSE",
    "SP_VOLUME",
}
FORBIDDEN_CAPTURE_FLAGS = (
    "growth_screen_applied",
    "current_survivor_filter_applied",
    "future_membership_filter_applied",
    "aov_109_reused",
    "legacy_identity_fallback_used",
)


@dataclass(frozen=True)
class Crv1StructuredSourceAdmission:
    identity_receipt: Mapping[str, Any]
    market_receipt: Mapping[str, Any]
    risk_set_source: Mapping[str, Any]
    risk_set_receipt: Mapping[str, Any]

    @property
    def eligible_security_count(self) -> int:
        return int(len(self.risk_set_source["rows"]))


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_crv1_structured_source_admission(
    *,
    as_of: datetime,
    identity_path: str | Path,
    identity_capture_receipt_path: str | Path,
    market_path: str | Path,
    market_capture_receipt_path: str | Path,
    identity_receipt_path_for_binding: str,
) -> Crv1StructuredSourceAdmission:
    """Derive CRV1 risk-set authority from independent broad CIQ custody.

    ``identity_receipt_path_for_binding`` is the path that will contain the
    returned structured identity receipt, expressed relative to the eventual
    risk-set receipt when possible.  The caller must serialize returned JSON
    with :func:`canonical_json_bytes` so the bound hash remains exact.
    """

    cutoff = _aware(as_of)
    identity_file = Path(identity_path)
    market_file = Path(market_path)
    identity_capture = _load_json(Path(identity_capture_receipt_path))
    market_capture = _load_json(Path(market_capture_receipt_path))

    identity_retrieved = _validate_capture_receipt(
        identity_capture,
        expected_schema=IDENTITY_CAPTURE_RECEIPT_SCHEMA,
        raw_path=identity_file,
        cutoff=cutoff,
        label="identity",
    )
    market_retrieved = _validate_capture_receipt(
        market_capture,
        expected_schema=MARKET_CAPTURE_RECEIPT_SCHEMA,
        raw_path=market_file,
        cutoff=cutoff,
        label="market",
    )
    if str(market_capture.get("identity_raw_object_sha256") or "") != sha256_file(identity_file):
        raise ValueError("alpha_pit_crv1_market_capture_identity_hash_mismatch")

    identity = pd.read_csv(identity_file, dtype=str).fillna("")
    missing_identity = sorted(IDENTITY_COLUMNS - set(identity.columns))
    if missing_identity:
        raise ValueError("alpha_pit_crv1_identity_columns_missing:" + ",".join(missing_identity))
    if identity.empty:
        raise ValueError("alpha_pit_crv1_identity_rows_required")

    master_rows: list[dict[str, Any]] = []
    seen_security_ids: set[str] = set()
    seen_trading_items: set[str] = set()
    for row in identity.to_dict(orient="records"):
        security_id = normalize_security_id(f"CIQSEC:{str(row['SP_CIQ_ID']).strip()}")
        trading_item_id = _nonempty(row["SPT_INSTRUMENT_ITEM_ID"], "trading_item_id")
        if security_id in seen_security_ids:
            raise ValueError("alpha_pit_crv1_identity_security_collision")
        if trading_item_id in seen_trading_items:
            raise ValueError("alpha_pit_crv1_identity_trading_item_collision")
        seen_security_ids.add(security_id)
        seen_trading_items.add(trading_item_id)
        master_rows.append(
            {
                "security_id": security_id,
                "company_id": "COMPANY:" + _nonempty(row["SP_ENTITY_ID"], "company_id"),
                "trading_item_id": trading_item_id,
                "primary_listing_id": _nonempty(row["PRIMARY_LISTING_ID"], "primary_listing_id"),
                "listing_country": str(row["LISTING_COUNTRY"]).strip().upper(),
                "primary_listing": _bool(row["PRIMARY_LISTING"], "primary_listing"),
                "security_class": str(row["SECURITY_CLASS"]).strip().upper(),
                "trading_status": str(row["TRADING_STATUS"]).strip().upper(),
                "identity_status": str(row["IDENTITY_STATUS"]).strip().upper(),
            }
        )

    market = pd.read_csv(market_file, dtype=str).fillna("")
    missing_market = sorted(MARKET_COLUMNS - set(market.columns))
    if missing_market:
        raise ValueError("alpha_pit_crv1_market_columns_missing:" + ",".join(missing_market))
    if market.empty:
        raise ValueError("alpha_pit_crv1_market_rows_required")
    market = market.copy()
    market["security_id"] = market["SP_CIQ_ID"].map(
        lambda value: normalize_security_id(f"CIQSEC:{str(value).strip()}")
    )
    market["trading_item_id"] = market["SPT_INSTRUMENT_ITEM_ID"].astype(str).str.strip()
    market["date"] = pd.to_datetime(market["SPT_DATE"], errors="coerce")
    market["close"] = pd.to_numeric(market["SP_PRICE_CLOSE"], errors="coerce")
    market["volume"] = pd.to_numeric(market["SP_VOLUME"], errors="coerce")
    market["total_return"] = pd.to_numeric(market["SP_TOTAL_RETURN"], errors="coerce")
    if market["date"].isna().any():
        raise ValueError("alpha_pit_crv1_market_date_invalid")
    if market.duplicated(["security_id", "date"]).any():
        raise ValueError("alpha_pit_crv1_market_duplicate_security_date")

    master_by_security = {row["security_id"]: row for row in master_rows}
    if not set(market["security_id"]).issubset(master_by_security):
        raise ValueError("alpha_pit_crv1_market_security_outside_identity")
    for row in market[["security_id", "trading_item_id"]].drop_duplicates().to_dict(orient="records"):
        expected = str(master_by_security[str(row["security_id"])]["trading_item_id"])
        if str(row["trading_item_id"]) != expected:
            raise ValueError("alpha_pit_crv1_market_trading_item_mismatch")

    available_market = market.loc[market["date"].dt.date <= cutoff.date()].copy()
    available_market["complete"] = available_market[["close", "volume", "total_return"]].notna().all(axis=1)
    history_counts = (
        available_market.loc[available_market["complete"]]
        .groupby("security_id")
        .size()
        .to_dict()
    )

    exclusion_counts: dict[str, int] = {}
    eligible_rows: list[dict[str, Any]] = []
    availability = max(identity_retrieved, market_retrieved)
    for row in master_rows:
        reason = _eligibility_exclusion_reason(row)
        history_count = int(history_counts.get(str(row["security_id"]), 0))
        if reason is None and history_count < int(RISK_SET_ELIGIBILITY_CONTRACT["minimum_prior_market_observations"]):
            reason = "INSUFFICIENT_200D_HISTORY"
        if reason is not None:
            exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
            continue
        eligible_rows.append(
            {
                **row,
                "prior_market_observation_count": history_count,
                "membership_effective_at": _utc_text(availability),
                "observed_at": _utc_text(availability),
                "available_at": _utc_text(availability),
                "eligibility_status": "ELIGIBLE",
            }
        )
    if not eligible_rows:
        raise ValueError("alpha_pit_crv1_risk_set_no_eligible_rows")
    eligible_rows.sort(key=lambda row: str(row["security_id"]))

    common_proof = {
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "structured_source_scope": CRV1_STRUCTURED_SOURCE_SCOPE,
        "growth_screen_applied": False,
        "current_survivor_filter_applied": False,
        "future_membership_filter_applied": False,
        "aov_109_reused": False,
        "legacy_identity_fallback_used": False,
    }
    identity_receipt = {
        "schema_version": CRV1_IDENTITY_RECEIPT_SCHEMA,
        "source_id": IDENTITY_SOURCE_ID,
        "provider": CIQ_PROVIDER,
        "retrieved_at": _utc_text(identity_retrieved),
        "raw_object_sha256": sha256_file(identity_file),
        "raw_object_name": identity_file.name,
        "capture_receipt_sha256": sha256_file(Path(identity_capture_receipt_path)),
        **common_proof,
    }
    identity_receipt_sha = sha256_bytes(canonical_json_bytes(identity_receipt))
    market_receipt = {
        "schema_version": CRV1_MARKET_RECEIPT_SCHEMA,
        "source_id": MARKET_SOURCE_ID,
        "provider": CIQ_PROVIDER,
        "retrieved_at": _utc_text(market_retrieved),
        "decision_target_date": available_market["date"].max().date().isoformat(),
        "raw_object_sha256": sha256_file(market_file),
        "raw_object_name": market_file.name,
        "capture_receipt_sha256": sha256_file(Path(market_capture_receipt_path)),
        "identity_receipt_sha256": identity_receipt_sha,
        **common_proof,
    }
    risk_set_source = {
        "schema_version": RISK_SET_SOURCE_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "eligibility_contract_id": RISK_SET_ELIGIBILITY_CONTRACT_ID,
        "eligibility_contract_sha256": RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
        "eligibility_contract": RISK_SET_ELIGIBILITY_CONTRACT,
        "identity_receipt_sha256": identity_receipt_sha,
        "as_of": _utc_text(cutoff),
        "growth_screen_applied": False,
        "current_survivor_filter_applied": False,
        "future_membership_filter_applied": False,
        "aov_109_reused": False,
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "rows": eligible_rows,
    }
    risk_source_sha = sha256_bytes(canonical_json_bytes(risk_set_source))
    risk_set_receipt = {
        "schema_version": RISK_SET_RECEIPT_SCHEMA,
        "source_id": CIQ_RISK_SET_SOURCE_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "eligibility_contract_id": RISK_SET_ELIGIBILITY_CONTRACT_ID,
        "eligibility_contract_sha256": RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
        "identity_receipt_path": _nonempty(identity_receipt_path_for_binding, "identity_receipt_path_for_binding"),
        "identity_receipt_sha256": identity_receipt_sha,
        "growth_screen_applied": False,
        "current_survivor_filter_applied": False,
        "future_membership_filter_applied": False,
        "aov_109_reused": False,
        "retrieved_at": _utc_text(availability),
        "observed_range_start": _utc_text(cutoff),
        "observed_range_end": _utc_text(cutoff),
        "raw_object_sha256": risk_source_sha,
    }
    return Crv1StructuredSourceAdmission(
        identity_receipt=identity_receipt,
        market_receipt=market_receipt,
        risk_set_source=risk_set_source,
        risk_set_receipt=risk_set_receipt,
    )


def _validate_capture_receipt(
    payload: Mapping[str, Any],
    *,
    expected_schema: str,
    raw_path: Path,
    cutoff: datetime,
    label: str,
) -> datetime:
    if payload.get("schema_version") != expected_schema:
        raise ValueError(f"alpha_pit_crv1_{label}_capture_receipt_schema_invalid")
    if payload.get("family_id") != FAMILY_ID or payload.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise ValueError(f"alpha_pit_crv1_{label}_capture_family_contract_invalid")
    if payload.get("capture_scope") != CAPTURE_SCOPE:
        raise ValueError(f"alpha_pit_crv1_{label}_capture_scope_invalid")
    provider = str(payload.get("provider") or "").strip().upper()
    if provider not in {"S&P CAPITAL IQ PRO", "S&P CAPITAL IQ", "SPCIQPRO"}:
        raise ValueError(f"alpha_pit_crv1_{label}_capture_provider_invalid")
    for field in FORBIDDEN_CAPTURE_FLAGS:
        if payload.get(field) is not False:
            raise ValueError(f"alpha_pit_crv1_{label}_capture_forbidden_flag:{field}")
    if sha256_file(raw_path) != str(payload.get("raw_object_sha256") or ""):
        raise ValueError(f"alpha_pit_crv1_{label}_capture_raw_hash_mismatch")
    retrieved = _timestamp(payload.get("retrieved_at"), f"{label}_retrieved_at")
    if retrieved > cutoff:
        raise ValueError(f"alpha_pit_crv1_{label}_capture_after_as_of")
    return retrieved


def _eligibility_exclusion_reason(row: Mapping[str, Any]) -> str | None:
    if str(row["listing_country"]) != "US":
        return "NON_US_LISTING"
    if row["primary_listing"] is not True:
        return "NOT_PRIMARY_LISTING"
    if str(row["security_class"]) != "COMMON_EQUITY":
        return "NOT_COMMON_EQUITY"
    if str(row["trading_status"]) != "ACTIVE_TRADABLE":
        return "NOT_ACTIVE_TRADABLE"
    if str(row["identity_status"]) != "UNIQUE_PERMANENT_MAPPING":
        return "IDENTITY_NOT_UNIQUE_PERMANENT_MAPPING"
    return None


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"alpha_pit_crv1_capture_receipt_invalid:{path.as_posix()}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("alpha_pit_crv1_capture_receipt_mapping_required")
    return payload


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("alpha_pit_crv1_as_of_timezone_required")
    return value.astimezone(UTC)


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"alpha_pit_crv1_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"alpha_pit_crv1_{field}_timezone_required")
    return parsed.astimezone(UTC)


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _nonempty(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"alpha_pit_crv1_{field}_required")
    return text


def _bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"alpha_pit_crv1_{field}_boolean_required")
