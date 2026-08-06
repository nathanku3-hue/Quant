"""Verified adapter for PAIR-DECISION-SERIES-1 episode 1.

One pinned Cboe BZX source capture, one permission manifest, and one XML-row
parser derive the MU and NVDA market packets at one common point-in-time cut.
Subject evidence is repository-banked only; this module performs no network I/O.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_v2_mu_nvda_reconciliation import load_verified_mu_nvda_reconciliation
from gv_portfolio_v0.market_packet import build_immutable_market_packet

PAIR_SYMBOLS = ("MU", "NVDA")
PARSER_IDENTITY = "GV_CBOE_BZX_SYMBOL_XML_ROW"
PARSER_VERSION = "1.0.0"
CAPTURE_PATH = Path(
    "data/gv_pair_decision_series/mu_nvda_episode_1/common_market_source_capture.json"
)
PERMISSION_PATH = Path(
    "data/gv_pair_decision_series/mu_nvda_episode_1/permission_manifest.json"
)
EPISODE_PATH = Path(
    "data/gv_pair_decision_series/mu_nvda_episode_1/episode_preregistration.json"
)
NVDA_DECISION_PATH = Path(
    "data/gv_pair_decision_series/mu_nvda_episode_1/nvda_subject_decision.json"
)
MU_RECONCILIATION_PATH = Path(
    "data/gv_v2_reconciliation/mu_nvda_supply_1/reconciliation_result.json"
)
NVDA_FACT_SET_PATH = Path(
    "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/fact_set.json"
)
EPISODE_PREREGISTRATION_SHA256 = (
    "1c2c93832e46be815cfa3875628448960286fcd3e4a8620d1388ff16bd8ad058"
)


class MarketSourceAdapterError(ValueError):
    """Fail-closed source, permission, parser, or subject-package error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _absolute(relative: Path) -> Path:
    root = _repo_root().resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise MarketSourceAdapterError("PAIR_SOURCE_PATH_ESCAPE") from exc
    return path


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MarketSourceAdapterError("PAIR_SOURCE_JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _load_json(relative: Path, *, expected_sha256: str | None = None) -> tuple[dict[str, Any], str]:
    path = _absolute(relative)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MarketSourceAdapterError("PAIR_SOURCE_FILE_UNAVAILABLE") from exc
    digest = _sha256_bytes(raw)
    if expected_sha256 is not None and digest != expected_sha256:
        raise MarketSourceAdapterError("PAIR_SOURCE_FILE_SHA256_MISMATCH")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarketSourceAdapterError("PAIR_SOURCE_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise MarketSourceAdapterError("PAIR_SOURCE_JSON_OBJECT_REQUIRED")
    return value, digest


def _required_text(mapping: Mapping[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise MarketSourceAdapterError(f"PAIR_SOURCE_{field.upper()}_REQUIRED")
    return value.strip()


def _exact_keys(mapping: Mapping[str, Any], expected: set[str], *, code: str) -> None:
    if set(mapping) != expected:
        raise MarketSourceAdapterError(code)


def load_verified_episode_contract() -> dict[str, Any]:
    episode, episode_sha = _load_json(
        EPISODE_PATH, expected_sha256=EPISODE_PREREGISTRATION_SHA256
    )
    required = {
        "schema_version",
        "decision_series_id",
        "episode_number",
        "decision_cut_id",
        "decision_cut_knowledge_at",
        "outcome_horizon_spec",
        "outcome_open_not_before",
        "comparator_spec",
        "cost_model_id",
        "decision_policy_version",
        "source_contract_version",
        "source_capture_path",
        "source_capture_sha256",
        "permission_manifest_path",
        "permission_manifest_sha256",
        "subject_evidence_policy",
        "mu_subject_evidence_path",
        "mu_subject_evidence_file_sha256",
        "nvda_subject_decision_path",
        "nvda_subject_decision_sha256",
        "outcome_status",
        "outcome_data_loaded",
        "claim_boundary",
    }
    _exact_keys(episode, required, code="PAIR_EPISODE_FIELD_SET_INVALID")
    if episode["schema_version"] != "gv_pair_decision_series_episode_v1":
        raise MarketSourceAdapterError("PAIR_EPISODE_SCHEMA_INVALID")
    if episode["decision_series_id"] != "PAIR_DECISION_SERIES_1":
        raise MarketSourceAdapterError("PAIR_EPISODE_SERIES_ID_INVALID")
    if episode["episode_number"] != 1:
        raise MarketSourceAdapterError("PAIR_EPISODE_NUMBER_INVALID")
    if episode["subject_evidence_policy"] != "BANKED_ONLY":
        raise MarketSourceAdapterError("PAIR_EPISODE_SUBJECT_POLICY_INVALID")
    if episode["outcome_status"] != "SEALED_NOT_OPENED":
        raise MarketSourceAdapterError("PAIR_EPISODE_OUTCOME_STATUS_INVALID")
    if episode["outcome_data_loaded"] is not False:
        raise MarketSourceAdapterError("PAIR_EPISODE_OUTCOME_DATA_PROHIBITED")
    if episode["source_contract_version"] != "CBOE_BZX_TWO_ROW_CAPTURE_V1":
        raise MarketSourceAdapterError("PAIR_EPISODE_SOURCE_CONTRACT_INVALID")
    result = deepcopy(episode)
    result["episode_preregistration_sha256"] = episode_sha
    return result


def _verify_subject_evidence(episode: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if episode["mu_subject_evidence_path"] != MU_RECONCILIATION_PATH.as_posix():
        raise MarketSourceAdapterError("PAIR_MU_EVIDENCE_PATH_INVALID")
    mu, _ = _load_json(
        MU_RECONCILIATION_PATH,
        expected_sha256=_required_text(episode, "mu_subject_evidence_file_sha256"),
    )
    verified_mu = load_verified_mu_nvda_reconciliation(
        result_path=_absolute(MU_RECONCILIATION_PATH)
    )
    if canonical_document_bytes(mu) != canonical_document_bytes(verified_mu):
        raise MarketSourceAdapterError("PAIR_MU_EVIDENCE_VERIFICATION_MISMATCH")
    if mu.get("portfolio_action") != "NO_POSITION" or mu.get(
        "portfolio_mutation_authorized"
    ) is not False:
        raise MarketSourceAdapterError("PAIR_MU_POSITIVE_AUTHORITY_PROHIBITED")

    if episode["nvda_subject_decision_path"] != NVDA_DECISION_PATH.as_posix():
        raise MarketSourceAdapterError("PAIR_NVDA_DECISION_PATH_INVALID")
    nvda, _ = _load_json(
        NVDA_DECISION_PATH,
        expected_sha256=_required_text(episode, "nvda_subject_decision_sha256"),
    )
    fact_set, fact_set_sha = _load_json(NVDA_FACT_SET_PATH)
    if nvda.get("source_evidence_path") != NVDA_FACT_SET_PATH.as_posix():
        raise MarketSourceAdapterError("PAIR_NVDA_EVIDENCE_PATH_INVALID")
    if nvda.get("source_evidence_file_sha256") != fact_set_sha:
        raise MarketSourceAdapterError("PAIR_NVDA_EVIDENCE_SHA256_MISMATCH")
    if nvda.get("source_evidence_identity") != fact_set.get("fact_set_hash"):
        raise MarketSourceAdapterError("PAIR_NVDA_FACT_SET_IDENTITY_MISMATCH")
    fact_ids = [str(row.get("fact_id")) for row in fact_set.get("facts") or []]
    if nvda.get("evidence_fact_ids") != fact_ids:
        raise MarketSourceAdapterError("PAIR_NVDA_FACT_SET_BINDING_MISMATCH")
    if (
        nvda.get("subject") != "NVDA"
        or nvda.get("outcome") != "ABSTAIN"
        or nvda.get("target_quantity") != "0"
        or nvda.get("portfolio_action") != "NO_POSITION"
    ):
        raise MarketSourceAdapterError("PAIR_NVDA_POSITIVE_AUTHORITY_PROHIBITED")
    return {"MU": mu, "NVDA": nvda}


def _parse_source_row(row: Mapping[str, Any]) -> dict[str, str]:
    expected = {
        "symbol",
        "row_locator",
        "raw_xml",
        "row_sha256",
        "permanent_instrument_identity",
        "value_field",
        "unit",
        "currency",
    }
    _exact_keys(row, expected, code="PAIR_SOURCE_ROW_FIELD_SET_INVALID")
    raw_xml = _required_text(row, "raw_xml")
    if _sha256_bytes(raw_xml.encode("utf-8")) != _required_text(row, "row_sha256"):
        raise MarketSourceAdapterError("PAIR_SOURCE_ROW_SHA256_MISMATCH")
    try:
        element = ElementTree.fromstring(raw_xml)
    except ElementTree.ParseError as exc:
        raise MarketSourceAdapterError("PAIR_SOURCE_ROW_XML_INVALID") from exc
    if element.tag != "symbol" or list(element):
        raise MarketSourceAdapterError("PAIR_SOURCE_ROW_XML_SHAPE_INVALID")
    symbol = _required_text(row, "symbol")
    if element.attrib.get("name") != symbol:
        raise MarketSourceAdapterError("PAIR_SOURCE_ROW_SYMBOL_MISMATCH")
    if row.get("value_field") != "last":
        raise MarketSourceAdapterError("PAIR_SOURCE_VALUE_FIELD_INVALID")
    value = element.attrib.get("last")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MarketSourceAdapterError("PAIR_SOURCE_VALUE_INVALID") from exc
    if not decimal_value.is_finite() or decimal_value <= 0:
        raise MarketSourceAdapterError("PAIR_SOURCE_VALUE_NOT_POSITIVE")
    return {
        "symbol": symbol,
        "row_locator": _required_text(row, "row_locator"),
        "row_sha256": _required_text(row, "row_sha256"),
        "permanent_instrument_identity": _required_text(
            row, "permanent_instrument_identity"
        ),
        "value": format(decimal_value, "f").rstrip("0").rstrip("."),
        "unit": _required_text(row, "unit"),
        "currency": _required_text(row, "currency"),
    }


def load_verified_pair_source() -> dict[str, Any]:
    episode = load_verified_episode_contract()
    permission_path = Path(_required_text(episode, "permission_manifest_path"))
    if permission_path != PERMISSION_PATH:
        raise MarketSourceAdapterError("PAIR_PERMISSION_PATH_INVALID")
    permission, permission_sha = _load_json(
        permission_path,
        expected_sha256=_required_text(episode, "permission_manifest_sha256"),
    )
    capture_path = Path(_required_text(episode, "source_capture_path"))
    if capture_path != CAPTURE_PATH:
        raise MarketSourceAdapterError("PAIR_CAPTURE_PATH_INVALID")
    capture, capture_sha = _load_json(
        capture_path,
        expected_sha256=_required_text(episode, "source_capture_sha256"),
    )
    if permission.get("source_capture_path") != capture_path.as_posix():
        raise MarketSourceAdapterError("PAIR_PERMISSION_CAPTURE_PATH_MISMATCH")
    if permission.get("source_capture_sha256") != capture_sha:
        raise MarketSourceAdapterError("PAIR_PERMISSION_CAPTURE_SHA256_MISMATCH")
    if permission.get("authorized_symbols") != list(PAIR_SYMBOLS):
        raise MarketSourceAdapterError("PAIR_PERMISSION_SYMBOLS_INVALID")
    if permission.get("authorized_fields") != ["last"]:
        raise MarketSourceAdapterError("PAIR_PERMISSION_FIELDS_INVALID")
    required_uses = {
        "internal_research_validation",
        "source_derived_market_packet",
        "certified_paper_decision_episode",
    }
    if not isinstance(permission.get("allowed_uses"), list) or not required_uses.issubset(
        set(permission["allowed_uses"])
    ):
        raise MarketSourceAdapterError("PAIR_PERMISSION_USE_INVALID")
    if capture.get("schema_version") != "gv_common_market_source_capture_v1":
        raise MarketSourceAdapterError("PAIR_CAPTURE_SCHEMA_INVALID")
    if capture.get("source_contract_version") != episode["source_contract_version"]:
        raise MarketSourceAdapterError("PAIR_CAPTURE_CONTRACT_MISMATCH")
    if capture.get("response_status") != 200 or capture.get(
        "response_content_type"
    ) != "text/xml":
        raise MarketSourceAdapterError("PAIR_CAPTURE_RESPONSE_INVALID")
    rows = capture.get("rows")
    if not isinstance(rows, list) or len(rows) != 2:
        raise MarketSourceAdapterError("PAIR_CAPTURE_TWO_ROWS_REQUIRED")
    parsed_rows = [_parse_source_row(row) for row in rows if isinstance(row, Mapping)]
    if len(parsed_rows) != 2 or tuple(row["symbol"] for row in parsed_rows) != PAIR_SYMBOLS:
        raise MarketSourceAdapterError("PAIR_CAPTURE_SYMBOL_ORDER_INVALID")
    subjects = _verify_subject_evidence(episode)
    return {
        "episode": episode,
        "capture": deepcopy(capture),
        "capture_sha256": capture_sha,
        "permission": deepcopy(permission),
        "permission_sha256": permission_sha,
        "rows": parsed_rows,
        "subjects": subjects,
    }


def load_source_derived_market_packets(
    instruments: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    source = load_verified_pair_source()
    by_symbol: dict[str, Mapping[str, Any]] = {}
    for instrument in instruments:
        symbol = str(instrument.get("symbol") or "")
        if symbol in by_symbol:
            raise MarketSourceAdapterError("PAIR_INSTRUMENT_SYMBOL_DUPLICATE")
        by_symbol[symbol] = instrument
    if tuple(by_symbol) != PAIR_SYMBOLS or set(by_symbol) != set(PAIR_SYMBOLS):
        raise MarketSourceAdapterError("PAIR_INSTRUMENT_SET_INVALID")

    rows_by_symbol = {row["symbol"]: row for row in source["rows"]}
    episode = source["episode"]
    packets: list[dict[str, str]] = []
    for symbol in PAIR_SYMBOLS:
        instrument = by_symbol[symbol]
        row = rows_by_symbol[symbol]
        permanent_key = str(instrument.get("permanent_key") or "")
        instrument_id = str(instrument.get("instrument_id") or "")
        if permanent_key != row["permanent_instrument_identity"]:
            raise MarketSourceAdapterError("PAIR_INSTRUMENT_PERMANENT_IDENTITY_MISMATCH")
        if not instrument_id:
            raise MarketSourceAdapterError("PAIR_INSTRUMENT_ID_REQUIRED")
        packets.append(
            build_immutable_market_packet(
                source_contract_version=str(episode["source_contract_version"]),
                source_object_identity=(
                    f"repo://{CAPTURE_PATH.as_posix()}"
                    f"#upstream_response_sha256={source['capture']['full_response_sha256']}"
                ),
                source_object_sha256=str(source["capture_sha256"]),
                permission_manifest_identity=f"repo://{PERMISSION_PATH.as_posix()}",
                permission_manifest_sha256=str(source["permission_sha256"]),
                parser_identity=PARSER_IDENTITY,
                parser_version=PARSER_VERSION,
                decision_cut_id=str(episode["decision_cut_id"]),
                row_locator=str(row["row_locator"]),
                row_sha256=str(row["row_sha256"]),
                valid_effective_at=str(source["capture"]["source_timestamp_utc"]),
                retrieval_knowledge_at=str(
                    source["capture"]["retrieval_knowledge_at"]
                ),
                permanent_instrument_identity=permanent_key,
                instrument_id=instrument_id,
                value=str(row["value"]),
                unit=str(row["unit"]),
                currency=str(row["currency"]),
            )
        )
    return packets


def verified_pair_summary() -> dict[str, Any]:
    source = load_verified_pair_source()
    return {
        "provider_identity": source["capture"]["provider_identity"],
        "source_contract_version": source["episode"]["source_contract_version"],
        "decision_cut_id": source["episode"]["decision_cut_id"],
        "valid_effective_at": source["capture"]["source_timestamp_utc"],
        "retrieval_knowledge_at": source["capture"]["retrieval_knowledge_at"],
        "source_object_sha256": source["capture_sha256"],
        "permission_manifest_sha256": source["permission_sha256"],
        "episode_preregistration_sha256": source["episode"][
            "episode_preregistration_sha256"
        ],
        "attribution": source["permission"]["attribution_required"],
        "symbols": list(PAIR_SYMBOLS),
    }
