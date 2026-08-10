"""SEC filing-claim adapter for ``alpha_pit_data_api_v1``.

Only explicitly landed SEC/company filing claims are returned.  When no claims
corpus is attached the adapter returns an empty, content-addressed artifact with
explicit missing-source coverage; it never substitutes generic web/news text.
"""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    CLAIM_TOPICS,
    FAMILY_ID,
    AlphaPITContractError,
    ArtifactRef,
    ResearchMode,
    iso_utc,
    validate_security_ids,
)
from research.alpha_pit_v1.manifests import build_artifact_ref


SEC_SOURCE_ID = "SEC:ALPHA_CLAIMS_V1"
SEC_SOURCE_SCHEMA = "alpha_pit_sec_claims_source_v1"
SEC_RECEIPT_SCHEMA = "alpha_pit_sec_claims_source_receipt_v1"


class SecAlphaClaimsV1Adapter:
    def __init__(
        self,
        *,
        source_path: str | Path | None = None,
        receipt_path: str | Path | None = None,
        custody_verified_at: datetime,
    ) -> None:
        if custody_verified_at.tzinfo is None or custody_verified_at.utcoffset() is None:
            raise AlphaPITContractError("alpha_pit_sec_custody_verified_at_timezone_required")
        if (source_path is None) != (receipt_path is None):
            raise AlphaPITContractError("alpha_pit_sec_source_pair_required")
        self._custody_verified_at = custody_verified_at.astimezone(UTC)
        self._parser_sha256 = _sha256_file(Path(__file__))
        self._source_path = Path(source_path) if source_path is not None else None
        self._receipt_path = Path(receipt_path) if receipt_path is not None else None
        self._receipt_payload: Mapping[str, Any] | None = None
        self._receipt_binding: Mapping[str, Any] | None = None
        self._receipt_sha256: str | None = None
        self._rows: list[Mapping[str, Any]] | None = None
        if self._source_path is not None and self._receipt_path is not None:
            self._load_landed_source()

    def source_claims(
        self,
        *,
        ids: Sequence[str],
        as_of: datetime,
        research_mode: ResearchMode,
    ) -> ArtifactRef:
        security_ids = validate_security_ids(ids)
        cutoff = _aware(as_of)
        if self._rows is None or self._receipt_binding is None or self._receipt_sha256 is None:
            binding = self._missing_binding(cutoff)
            coverage = {
                "requested_security_count": len(security_ids),
                "returned_security_count": 0,
                "requested_field_count": None,
                "present_count": 0,
                "missing_count": len(security_ids),
                "not_entitled_count": 0,
                "stale_count": 0,
                "coverage_rate": "0",
                "missingness_by_reason": {"SEC_CLAIMS_CAPTURE_NOT_LANDED": len(security_ids)},
            }
            return build_artifact_ref(
                artifact_type="SOURCE_CLAIMS",
                research_mode=research_mode,
                request={"ids": list(security_ids), "as_of": iso_utc(cutoff)},
                payload={
                    "family_id": FAMILY_ID,
                    "as_of": iso_utc(cutoff),
                    "rows": [],
                    "row_count": 0,
                    "coverage_status": "MISSING_SOURCE",
                    "missingness_reason": "SEC_CLAIMS_CAPTURE_NOT_LANDED",
                },
                as_of=cutoff,
                created_at=cutoff,
                source_receipts=[binding],
                coverage_summary=coverage,
            )

        requested = set(security_ids)
        admitted: list[dict[str, Any]] = []
        covered: set[str] = set()
        for raw in self._rows:
            security_id = str(raw["security_id"])
            if security_id not in requested:
                continue
            available = _parse_timestamp(raw.get("available_at"), field="claim_available_at")
            if available > cutoff:
                continue
            observed = _parse_timestamp(raw.get("observed_at"), field="claim_observed_at")
            topic = str(raw.get("claim_topic") or "")
            if topic not in CLAIM_TOPICS:
                raise AlphaPITContractError("alpha_pit_sec_claim_topic_invalid")
            body = {
                "claim_id": str(raw.get("claim_id") or domain_hash(
                    "ALPHA_PIT_V1:SEC:CLAIM_ID",
                    {
                        "security_id": security_id,
                        "source_document_id": str(raw.get("source_document_id") or ""),
                        "source_locator": str(raw.get("source_locator") or ""),
                        "claim_normalized": str(raw.get("claim_normalized") or ""),
                    },
                )),
                "security_id": security_id,
                "related_security_id": _optional_text(raw.get("related_security_id")),
                "claim_topic": topic,
                "claim_normalized": str(raw.get("claim_normalized") or "").strip(),
                "claim_direction": str(raw.get("claim_direction") or "").strip(),
                "claim_horizon": str(raw.get("claim_horizon") or "").strip(),
                "source_document_id": str(raw.get("source_document_id") or "").strip(),
                "source_document_type": str(raw.get("source_document_type") or "").strip(),
                "source_locator": str(raw.get("source_locator") or "").strip(),
                "source_published_at": _timestamp_text(raw.get("source_published_at"), field="claim_source_published_at"),
                "source_accepted_at": _timestamp_text(raw.get("source_accepted_at"), field="claim_source_accepted_at"),
                "observed_at": iso_utc(observed),
                "available_at": iso_utc(available),
                "source_receipt_sha256": self._receipt_sha256,
                "extraction_procedure_id": str(raw.get("extraction_procedure_id") or "").strip(),
                "extraction_procedure_sha256": str(raw.get("extraction_procedure_sha256") or "").strip(),
                "schema_version": "alpha_pit_source_claim_row_v1",
                "epistemic_class": "OBSERVED_SOURCE_CLAIM",
                "coverage_status": "PRESENT",
            }
            required_text = (
                "claim_normalized",
                "claim_direction",
                "claim_horizon",
                "source_document_id",
                "source_document_type",
                "source_locator",
                "extraction_procedure_id",
                "extraction_procedure_sha256",
            )
            if any(not str(body[key]).strip() for key in required_text):
                raise AlphaPITContractError("alpha_pit_sec_claim_required_field_blank")
            if len(str(body["extraction_procedure_sha256"])) != 64:
                raise AlphaPITContractError("alpha_pit_sec_claim_procedure_hash_invalid")
            row = {**body, "artifact_row_hash": domain_hash("ALPHA_PIT_V1:SEC:CLAIM_ROW", body)}
            admitted.append(row)
            covered.add(security_id)

        missing_count = len(requested - covered)
        coverage = {
            "requested_security_count": len(security_ids),
            "returned_security_count": len(covered),
            "requested_field_count": None,
            "present_count": len(admitted),
            "missing_count": missing_count,
            "not_entitled_count": 0,
            "stale_count": 0,
            "coverage_rate": format(len(covered) / len(security_ids) if security_ids else 1.0, ".17g"),
            "missingness_by_reason": {"NO_ADMITTED_SEC_CLAIM_AT_AS_OF": missing_count} if missing_count else {},
        }
        return build_artifact_ref(
            artifact_type="SOURCE_CLAIMS",
            research_mode=research_mode,
            request={"ids": list(security_ids), "as_of": iso_utc(cutoff)},
            payload={"family_id": FAMILY_ID, "as_of": iso_utc(cutoff), "rows": admitted, "row_count": len(admitted)},
            as_of=cutoff,
            created_at=_parse_timestamp(self._receipt_binding["retrieved_at"], field="receipt_retrieved_at"),
            source_receipts=[self._receipt_binding],
            coverage_summary=coverage,
        )

    def _load_landed_source(self) -> None:
        assert self._source_path is not None and self._receipt_path is not None
        source = _load_json(self._source_path)
        receipt = _load_json(self._receipt_path)
        if source.get("schema_version") != SEC_SOURCE_SCHEMA:
            raise AlphaPITContractError("alpha_pit_sec_source_schema_invalid")
        if receipt.get("schema_version") != SEC_RECEIPT_SCHEMA or receipt.get("source_id") != SEC_SOURCE_ID:
            raise AlphaPITContractError("alpha_pit_sec_receipt_contract_invalid")
        if _sha256_file(self._source_path) != str(receipt.get("raw_object_sha256") or ""):
            raise AlphaPITContractError("alpha_pit_sec_source_hash_mismatch")
        rows = source.get("rows")
        if not isinstance(rows, list):
            raise AlphaPITContractError("alpha_pit_sec_source_rows_required")
        normalized: list[Mapping[str, Any]] = []
        for raw in rows:
            if not isinstance(raw, Mapping):
                raise AlphaPITContractError("alpha_pit_sec_source_row_mapping_required")
            security_id = validate_security_ids([str(raw.get("security_id") or "")])[0]
            normalized.append({**raw, "security_id": security_id})
        retrieved_at = _timestamp_text(receipt.get("retrieved_at"), field="receipt_retrieved_at")
        receipt_sha = _sha256_file(self._receipt_path)
        self._receipt_payload = receipt
        self._receipt_sha256 = receipt_sha
        self._receipt_binding = {
            "source_id": SEC_SOURCE_ID,
            "provider": "SEC / issuer filings",
            "retrieved_at": retrieved_at,
            "observed_range_start": _optional_text(receipt.get("observed_range_start")),
            "observed_range_end": _optional_text(receipt.get("observed_range_end")),
            "raw_receipt_path": self._receipt_path.as_posix(),
            "raw_receipt_sha256": receipt_sha,
            "parser_id": "SecAlphaClaimsV1Adapter:claims_v1",
            "parser_sha256": self._parser_sha256,
            "license_scope": "PUBLIC_FILING_SOURCE",
            "retention_class": "IMMUTABLE_SOURCE_CLAIM_EVIDENCE",
        }
        self._rows = normalized

    def _missing_binding(self, observed_at: datetime) -> Mapping[str, Any]:
        body = {
            "schema_version": "alpha_pit_missing_source_receipt_v1",
            "source_id": SEC_SOURCE_ID,
            "reason": "SEC_CLAIMS_CAPTURE_NOT_LANDED",
            "retrieved_at": iso_utc(observed_at),
        }
        digest = domain_hash("ALPHA_PIT_V1:MISSING_SOURCE_RECEIPT", body)
        return {
            "source_id": SEC_SOURCE_ID,
            "provider": "LOCAL_CUSTODY_SENTINEL_NO_SOURCE_DOCUMENTS",
            "retrieved_at": body["retrieved_at"],
            "observed_range_start": None,
            "observed_range_end": None,
            "raw_receipt_path": f"missing/SEC_ALPHA_CLAIMS_V1/{digest}.json",
            "raw_receipt_sha256": digest,
            "parser_id": "SecAlphaClaimsV1Adapter:claims_missing_v1",
            "parser_sha256": self._parser_sha256,
            "license_scope": "NO_SOURCE_DOCUMENT_BYTES_CAPTURED",
            "retention_class": "MECHANICAL_MISSINGNESS_SENTINEL",
        }


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise AlphaPITContractError("alpha_pit_sec_as_of_timezone_required")
    return value.astimezone(UTC)


def _timestamp_text(value: Any, *, field: str) -> str:
    return iso_utc(_parse_timestamp(value, field=field))


def _parse_timestamp(value: Any, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AlphaPITContractError(f"alpha_pit_sec_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AlphaPITContractError(f"alpha_pit_sec_{field}_timezone_required")
    return parsed.astimezone(UTC)


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise AlphaPITContractError(f"alpha_pit_sec_file_missing:{path.as_posix()}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AlphaPITContractError(f"alpha_pit_sec_json_invalid:{path.as_posix()}") from exc
    if not isinstance(payload, Mapping):
        raise AlphaPITContractError("alpha_pit_sec_json_mapping_required")
    return payload


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        raise AlphaPITContractError(f"alpha_pit_sec_file_missing:{path.as_posix()}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
