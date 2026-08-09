"""Fail-closed historical primary-security identity admission for Lane 2.

Formal historical AOV evidence must not map a historical company cohort through
whatever security happens to be primary at the later retrieval date.  The
historical-start primary security/trading-item mapping is therefore a separate,
hash-bound provider object whose effective date must equal the A1 decision
start.  A current-primary export remains useful for diagnostics but cannot
satisfy this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


HISTORICAL_SECURITY_MASTER_SOURCE_ID = "SPCIQPRO:HISTORICAL_PRIMARY_SECURITY_MASTER"
HISTORICAL_SECURITY_MASTER_RECEIPT_SCHEMA = "aov0_ciq_historical_primary_security_master_receipt_v1"
HISTORICAL_SECURITY_MASTER_CAPTURE_MODE = "HISTORICAL_PIT_PRIMARY_SECURITY_SNAPSHOT"
HISTORICAL_SECURITY_MASTER_FREEZE_MODE = "HISTORICAL_START_PRIMARY_SECURITY_FROZEN"
HISTORICAL_SECURITY_MASTER_SELECTION = "PROVIDER_PRIMARY_AS_OF_REQUESTED_CUTOFF"

REQUIRED_IDENTITY_COLUMNS = (
    "SP_ENTITY_ID",
    "SP_SECURITY_ID",
    "SP_CIQ_ID",
    "SPT_INSTRUMENT_ITEM_ID",
    "SP_TRADING_ITEM_ID",
)


class HistoricalSecurityMasterError(ValueError):
    """Fail-closed historical security-master admission error."""


@dataclass(frozen=True)
class HistoricalSecurityMaster:
    entity_ids: tuple[str, ...]
    security_ids: tuple[str, ...]
    trading_item_ids: tuple[str, ...]
    as_of_date: pd.Timestamp
    master_path: Path
    receipt_path: Path
    metadata: dict[str, Any]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_historical_start_security_master(
    master_path: str | Path,
    receipt_path: str | Path,
    *,
    expected_as_of_date: str | pd.Timestamp,
    expected_entity_ids: Iterable[object],
) -> HistoricalSecurityMaster:
    """Admit one exact historical-start primary-security provider snapshot.

    The receipt must mechanically bind the provider-effective date to the A1
    start date and explicitly state that the object is not conditioned on the
    later/current primary mapping.  Raw identity rows must be a one-to-one
    mapping for exactly the admitted historical company cohort.
    """

    master_path = Path(master_path)
    receipt_path = Path(receipt_path)
    if not master_path.is_file():
        raise FileNotFoundError(master_path)
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HistoricalSecurityMasterError("historical_security_master_receipt_json_invalid") from exc

    if receipt.get("schema_version") != HISTORICAL_SECURITY_MASTER_RECEIPT_SCHEMA:
        raise HistoricalSecurityMasterError("historical_security_master_receipt_schema_invalid")
    if receipt.get("source_id") != HISTORICAL_SECURITY_MASTER_SOURCE_ID:
        raise HistoricalSecurityMasterError("historical_security_master_source_invalid")
    if receipt.get("capture_mode") != HISTORICAL_SECURITY_MASTER_CAPTURE_MODE:
        raise HistoricalSecurityMasterError("historical_security_master_capture_mode_invalid")
    if receipt.get("identity_freeze_mode") != HISTORICAL_SECURITY_MASTER_FREEZE_MODE:
        raise HistoricalSecurityMasterError("historical_security_master_freeze_mode_invalid")
    if receipt.get("primary_security_selection") != HISTORICAL_SECURITY_MASTER_SELECTION:
        raise HistoricalSecurityMasterError("historical_security_master_selection_invalid")
    if receipt.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalSecurityMasterError("historical_security_master_asof_not_mechanically_bound")
    if receipt.get("current_primary_conditioned") is not False:
        raise HistoricalSecurityMasterError("historical_security_master_current_primary_conditioning_forbidden")
    if receipt.get("financial_alpha_evidence") != 0:
        raise HistoricalSecurityMasterError("historical_security_master_financial_alpha_evidence_invalid")
    if receipt.get("prospective_clock_authority") != "NONE":
        raise HistoricalSecurityMasterError("historical_security_master_prospective_authority_invalid")
    if receipt.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalSecurityMasterError("historical_security_master_mutation_authority_invalid")
    if receipt.get("security_id_source_metric") != "SP_CIQ_ID":
        raise HistoricalSecurityMasterError("historical_security_master_security_metric_invalid")
    if receipt.get("trading_item_source_metric") != "SP_TRADING_ITEM_ID":
        raise HistoricalSecurityMasterError("historical_security_master_trading_metric_invalid")

    expected_date = pd.Timestamp(expected_as_of_date).normalize()
    for field in ("requested_cutoff_date", "provider_effective_as_of_date"):
        try:
            observed = pd.Timestamp(receipt.get(field)).normalize()
        except Exception as exc:  # pragma: no cover - pandas exception is version-specific.
            raise HistoricalSecurityMasterError(f"historical_security_master_{field}_invalid") from exc
        if observed != expected_date:
            raise HistoricalSecurityMasterError(f"historical_security_master_{field}_mismatch")

    raw_hash = _sha256_file(master_path)
    if receipt.get("raw_object_sha256") != raw_hash:
        raise HistoricalSecurityMasterError("historical_security_master_hash_mismatch")
    if receipt.get("raw_object_name") != master_path.name:
        raise HistoricalSecurityMasterError("historical_security_master_name_mismatch")
    if int(receipt.get("raw_object_bytes", -1)) != master_path.stat().st_size:
        raise HistoricalSecurityMasterError("historical_security_master_size_mismatch")

    frame = pd.read_csv(master_path, dtype=str, encoding="utf-8-sig")
    missing = sorted(set(REQUIRED_IDENTITY_COLUMNS) - set(frame.columns))
    if missing:
        raise HistoricalSecurityMasterError(
            "historical_security_master_identity_columns_missing:" + ",".join(missing)
        )
    if frame.empty:
        raise HistoricalSecurityMasterError("historical_security_master_empty")

    identity = frame.loc[:, list(REQUIRED_IDENTITY_COLUMNS)].fillna("").astype(str)
    for column in REQUIRED_IDENTITY_COLUMNS:
        identity[column] = identity[column].str.strip()
        if identity[column].eq("").any():
            raise HistoricalSecurityMasterError(f"historical_security_master_identity_blank:{column}")
        if identity[column].duplicated().any():
            raise HistoricalSecurityMasterError(f"historical_security_master_identity_duplicate:{column}")

    if not identity["SP_ENTITY_ID"].str.fullmatch(r"\d+").all():
        raise HistoricalSecurityMasterError("historical_security_master_entity_id_invalid")
    if not identity["SP_CIQ_ID"].str.fullmatch(r"IQ\d+").all():
        raise HistoricalSecurityMasterError("historical_security_master_ciq_id_invalid")
    if not identity["SP_TRADING_ITEM_ID"].str.fullmatch(r"\d+").all():
        raise HistoricalSecurityMasterError("historical_security_master_trading_item_id_invalid")
    if not identity["SPT_INSTRUMENT_ITEM_ID"].str.fullmatch(r"SPT\d+").all():
        raise HistoricalSecurityMasterError("historical_security_master_instrument_item_id_invalid")
    if not identity["SP_SECURITY_ID"].eq(identity["SP_CIQ_ID"]).all():
        raise HistoricalSecurityMasterError("historical_security_master_security_id_alias_mismatch")
    expected_spt = "SPT" + identity["SP_TRADING_ITEM_ID"]
    if not identity["SPT_INSTRUMENT_ITEM_ID"].eq(expected_spt).all():
        raise HistoricalSecurityMasterError("historical_security_master_trading_item_alias_mismatch")

    expected_entities = tuple(sorted(str(value).strip() for value in expected_entity_ids))
    if (
        not expected_entities
        or any(not value for value in expected_entities)
        or len(expected_entities) != len(set(expected_entities))
    ):
        raise HistoricalSecurityMasterError("historical_security_master_expected_entities_invalid")
    entity_ids = tuple(sorted(identity["SP_ENTITY_ID"].tolist()))
    if entity_ids != expected_entities:
        raise HistoricalSecurityMasterError("historical_security_master_entity_membership_mismatch")
    if int(receipt.get("result_count", -1)) != len(entity_ids):
        raise HistoricalSecurityMasterError("historical_security_master_result_count_mismatch")

    observed_columns = tuple(str(value) for value in receipt.get("observed_identity_columns") or ())
    if not set(REQUIRED_IDENTITY_COLUMNS).issubset(observed_columns):
        raise HistoricalSecurityMasterError("historical_security_master_identity_authority_missing")

    security_ids = tuple(
        identity.sort_values("SP_ENTITY_ID")["SP_CIQ_ID"].map(lambda value: f"CIQSEC:{value}").tolist()
    )
    trading_item_ids = tuple(
        identity.sort_values("SP_ENTITY_ID")["SP_TRADING_ITEM_ID"].tolist()
    )
    metadata = {
        "source_id": HISTORICAL_SECURITY_MASTER_SOURCE_ID,
        "capture_mode": HISTORICAL_SECURITY_MASTER_CAPTURE_MODE,
        "identity_freeze_mode": HISTORICAL_SECURITY_MASTER_FREEZE_MODE,
        "primary_security_selection": HISTORICAL_SECURITY_MASTER_SELECTION,
        "historical_primary_security_identity_reconstructed": True,
        "as_of_date": expected_date.date().isoformat(),
        "entity_count": len(entity_ids),
        "master_path": master_path.resolve().as_posix(),
        "master_sha256": raw_hash,
        "receipt_path": receipt_path.resolve().as_posix(),
        "receipt_sha256": _sha256_file(receipt_path),
        "current_primary_conditioned": False,
        "financial_alpha_evidence": 0,
    }
    return HistoricalSecurityMaster(
        entity_ids=entity_ids,
        security_ids=security_ids,
        trading_item_ids=trading_item_ids,
        as_of_date=expected_date,
        master_path=master_path,
        receipt_path=receipt_path,
        metadata=metadata,
    )
