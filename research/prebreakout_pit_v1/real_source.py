"""Deterministic real-source compiler for PREBREAKOUT W3 custody.

This module converts the already-landed Capital IQ market/listing and filtered
Key Developments bytes into date-local W3 inputs.  It performs no provider
queries, outcome access, model scoring, trial charging, W6 label reads, or
broker actions.

The lifecycle compiler is deliberately conservative.  Key Developments are
company-linked, while W3 eligibility is exact-listing keyed.  Company linkage
is therefore used only to propagate a corporate-action *state* to the exact
CIQSEC + Trading Item rows that the independent dated Securities query already
proved.  It never chooses or repairs listing identity.

Key Developments expose event dates but not trustworthy intraday publication
stamps.  The first captured dated market/listing snapshot is the lifecycle
baseline: older events cannot override an exact listing that the provider proves
active on that first session.  From that baseline forward, an event can affect
W3 authority only on the first captured market session strictly after its
EVENT_DATE.  M&A role is
resolved from the event headline only when the entity's source-captured ticker
anchor proves buyer/seller versus whole-company target position.  Ticker is a
text-role clue here, never risky-asset identity and never a listing fallback.
Ambiguous potentially-terminal role/state fails closed as UNRESOLVED.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from research.prebreakout_discovery_v1.preregistration import CONTRACT_SHA256 as W2_CONTRACT_SHA256
from research.prebreakout_pit_v1.authority import (
    ACTION_CLEAR,
    ACTION_EFFECTIVE_TERMINAL,
    ACTION_UNRESOLVED,
    AMBIGUOUS_DATE_LOCAL,
    CANDIDATE_ROW_SCHEMA,
    CORPORATE_ACTION_ROW_SCHEMA,
    HISTORICAL_CAPTURE_MODE,
    PRIMARY_DATE_LOCAL,
    PRIMARY_PROOF_AMBIGUOUS,
    PRIMARY_PROOF_UNIQUE,
    RISK_SET_SPEC_ID,
    SOURCE_AUTHORITY_SCHEMA,
)


REAL_SOURCE_MANIFEST_SCHEMA = "prebreakout_w3_real_source_manifest_v1"
SESSION_PARTITION_SCHEMA = "prebreakout_w3_session_partition_v1"
LIFECYCLE_STATE_RECEIPT_SCHEMA = "prebreakout_w3_lifecycle_state_receipt_v1"
REAL_SOURCE_COMPILER_ID = "PREBREAKOUT_W3_REAL_SOURCE_COMPILER_V1"
FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
PROVIDER = "S&P Capital IQ Pro"
MARKET_SOURCE_ID = "SPCIQPRO:SECURITIES_PRODUCTQUERY"
LIFECYCLE_SOURCE_ID = "SPCIQPRO:KEY_DEVELOPMENTS_DATE_LOCAL_STATE"
LICENSE_SCOPE = "SPCIQPRO_LOCAL_RESEARCH_ENTITLEMENT"
RETENTION_CLASS = "LOCAL_RESEARCH_CUSTODY"

EXPECTED_SESSION_COUNT = 346
EXPECTED_MARKET_ROW_COUNT = 1_894_207
EXPECTED_COMPANY_COUNT = 5_919
EXPECTED_LISTING_COUNT = 6_018
EXPECTED_MISSING_CLOSE = 0
EXPECTED_MISSING_TOTAL_RETURN = 177_820
EXPECTED_MISSING_VOLUME = 0
EXPECTED_LIFECYCLE_PART_COUNT = 12
EXPECTED_LIFECYCLE_ROW_COUNT = 176_353

WARMUP_SESSION_COUNT = 60
W5_DEVELOPMENT_SESSION_COUNT = 226
POST_DEVELOPMENT_EMBARGO_SESSION_COUNT = 20
W6_LOCKBOX_DECISION_COUNT = 20
LOCKBOX_LABEL_TAIL_COUNT = 20

MNA_ANNOUNCEMENT = "M&A: Transaction Announcement"
MNA_CLOSING = "M&A: Transaction Closing"
MNA_CANCELLATION = "M&A: Transaction Cancellation"
DELISTING = "Delisting"
STOCK_SPLIT = "Stock Splits or Significant Stock Dividend"
TICKER_CHANGE = "Ticker Change"
EXCHANGE_CHANGE = "Exchange Change"
BANKRUPTCY_FILING = "Bankruptcy: Filing"
BANKRUPTCY_EMERGENCE = "Bankruptcy: Emergence or Exit"
BANKRUPTCY_CONCLUSION = "Bankruptcy: Conclusion"
BANKRUPTCY_LIQUIDATION = "Bankruptcy: Asset Sale or Liquidation"

_EVENT_PRIORITY = {
    "NOOP": 0,
    "CLEAR_IF_MNA_UNRESOLVED": 10,
    "CLEAR_IF_DELISTING_UNRESOLVED": 10,
    "CLEAR_IF_BANKRUPTCY_UNRESOLVED": 10,
    "SET_UNRESOLVED": 20,
    "SET_EFFECTIVE": 30,
}

_NONTERMINAL_TARGET_OBJECT_RE = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s*%|minority\s+stake|majority\s+stake|stake\s+in|"
    r"assets?\s+(?:of|from)|business\s+(?:of|from)|division\s+(?:of|from)|"
    r"portfolio\s+(?:of|from)|facilit(?:y|ies)\s+(?:of|from)|site\s+(?:of|from)|"
    r"brand\s+(?:of|from)|operations?\s+(?:of|from))\b",
    re.IGNORECASE,
)
_MNA_VERB_RE = re.compile(
    r"\b(?:acquire(?:d|s|ing)?|acquisition\s+of|offer\s+to\s+acquire|"
    r"bid\s+to\s+acquire|agreement\s+to\s+acquire|interest\s+to\s+acquire)\b",
    re.IGNORECASE,
)
_MNA_ACQUIRER_AFTER_ANCHOR_RE = re.compile(
    r"\b(?:agreed\s+to\s+acquire|entered\b[^.;]{0,100}\bto\s+acquire|"
    r"completed\s+the\s+acquisition|completed\s+acquisition|acquired|"
    r"submitted\b[^.;]{0,120}\binterest\s+to\s+acquire|"
    r"signed\b[^.;]{0,120}\bto\s+acquire|made\s+an\s+offer\s+to\s+acquire)\b",
    re.IGNORECASE,
)
_MNA_TARGET_AFTER_ANCHOR_RE = re.compile(
    r"\b(?:to\s+be\s+acquired|was\s+acquired|is\s+being\s+acquired|"
    r"will\s+be\s+acquired)\b",
    re.IGNORECASE,
)

_DELIST_NONTERMINAL_RE = re.compile(
    r"\b(?:regains?\s+compliance|non[- ]compliance|deficien(?:cy|t)|"
    r"minimum\s+bid\s+price|minimum\s+stockholders?'?\s+equity|"
    r"continued\s+listing|reverse\s+(?:share|stock)\s+split|share\s+consolidation|"
    r"transfer(?:s|red|ring)?\s+(?:of\s+)?(?:its\s+)?(?:listing|ads)|"
    r"extension\b[^.;]{0,120}\bregain\s+compliance)\b",
    re.IGNORECASE,
)
_DELIST_EFFECTIVE_RE = re.compile(
    r"\b(?:stock|shares?|securities|common\s+stock|ads(?:s)?)\b[^.;]{0,80}"
    r"\b(?:delists?|delisted|deleted\s+from)\b|"
    r"\b(?:files?|filed)\s+(?:a\s+)?form\s+15\b|"
    r"\bno\s+longer\s+(?:be\s+)?(?:listed|traded)\b",
    re.IGNORECASE,
)
_DELIST_PENDING_RE = re.compile(
    r"\b(?:to\s+delist|will\s+(?:be\s+)?delist|requests?\b[^.;]{0,120}\bdelist|"
    r"commence\s+delisting|determines?\s+to\s+delist|delist\s+determination|"
    r"to\s+no\s+longer\s+be\s+(?:listed|traded)|"
    r"will\s+no\s+longer\s+be\s+(?:listed|traded))\b",
    re.IGNORECASE,
)


class RealSourceCompileError(ValueError):
    """Fail-closed real-source compilation error."""


@dataclass(frozen=True)
class LifecycleTransition:
    entity_id: str
    source_event_date: str
    activation_session: str
    transition_kind: str
    state_event_type: str
    event_oid: str
    raw_event_type: str
    role_resolution: str
    headline: str

    def as_dict(self) -> dict[str, str]:
        return {
            "entity_id": self.entity_id,
            "source_event_date": self.source_event_date,
            "activation_session": self.activation_session,
            "transition_kind": self.transition_kind,
            "state_event_type": self.state_event_type,
            "event_oid": self.event_oid,
            "raw_event_type": self.raw_event_type,
            "role_resolution": self.role_resolution,
            "headline": self.headline,
        }


@dataclass(frozen=True)
class LifecycleState:
    action_state: str = ACTION_CLEAR
    effective_session_date: str | None = None
    event_type: str = "NONE"
    source_event_date: str | None = None
    event_oid: str | None = None
    role_resolution: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_state": self.action_state,
            "effective_session_date": self.effective_session_date,
            "event_type": self.event_type,
            "source_event_date": self.source_event_date,
            "event_oid": self.event_oid,
            "role_resolution": self.role_resolution,
        }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def freeze_session_partition(session_spine: Sequence[str]) -> dict[str, Any]:
    sessions = [str(value) for value in session_spine]
    if len(sessions) != EXPECTED_SESSION_COUNT or len(set(sessions)) != len(sessions):
        raise RealSourceCompileError("prebreakout_real_source_session_spine_count_invalid")
    if sessions != sorted(sessions):
        raise RealSourceCompileError("prebreakout_real_source_session_spine_not_sorted")
    for value in sessions:
        if date.fromisoformat(value).isoformat() != value:
            raise RealSourceCompileError("prebreakout_real_source_session_date_invalid")

    i0 = 0
    i1 = i0 + WARMUP_SESSION_COUNT
    i2 = i1 + W5_DEVELOPMENT_SESSION_COUNT
    i3 = i2 + POST_DEVELOPMENT_EMBARGO_SESSION_COUNT
    i4 = i3 + W6_LOCKBOX_DECISION_COUNT
    i5 = i4 + LOCKBOX_LABEL_TAIL_COUNT
    if i5 != len(sessions):
        raise RealSourceCompileError("prebreakout_real_source_partition_not_exhaustive")

    body: dict[str, Any] = {
        "schema_version": SESSION_PARTITION_SCHEMA,
        "family_id": FAMILY_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "total_session_count": len(sessions),
        "feature_warmup": sessions[i0:i1],
        "w5_development": sessions[i1:i2],
        "post_development_embargo": sessions[i2:i3],
        "w6_lockbox_decisions": sessions[i3:i4],
        "lockbox_label_maturity_tail": sessions[i4:i5],
        "development_labels_overlap_w6_lockbox": False,
        "w6_labels_opened": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {**body, "partition_sha256": canonical_sha256(body)}


def verify_and_build_custody_manifest(
    *,
    market_dirs: Sequence[str | Path],
    lifecycle_dir: str | Path,
) -> dict[str, Any]:
    market_files: list[Path] = []
    for raw_dir in market_dirs:
        directory = Path(raw_dir)
        if not directory.is_dir():
            raise FileNotFoundError(directory)
        market_files.extend(directory.glob("date_*.csv"))
    market_files = sorted(market_files, key=lambda path: path.name)
    if len(market_files) != EXPECTED_SESSION_COUNT:
        raise RealSourceCompileError("prebreakout_real_source_market_part_count_invalid")

    session_spine: list[str] = []
    company_ids: set[str] = set()
    listing_ids: set[tuple[str, str]] = set()
    market_rows = 0
    missing_close = 0
    missing_total_return = 0
    missing_volume = 0
    market_parts: list[dict[str, Any]] = []

    for csv_path in market_files:
        receipt_path = csv_path.with_suffix(".receipt.json")
        if not receipt_path.is_file():
            raise FileNotFoundError(receipt_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        csv_hash = sha256_file(csv_path)
        receipt_hash = sha256_file(receipt_path)
        if receipt.get("raw_object_sha256") != csv_hash:
            raise RealSourceCompileError("prebreakout_real_source_market_raw_hash_mismatch")
        if receipt.get("w2_contract_sha256") != W2_CONTRACT_SHA256:
            raise RealSourceCompileError("prebreakout_real_source_market_w2_hash_mismatch")
        if receipt.get("current_primary_conditioned") is not False or receipt.get("current_survivor_conditioned") is not False:
            raise RealSourceCompileError("prebreakout_real_source_market_current_state_forbidden")
        if receipt.get("primary_issue_field_requested") is not False:
            raise RealSourceCompileError("prebreakout_real_source_market_current_primary_field_forbidden")
        session = str(receipt.get("session_date") or "")
        if not session:
            raise RealSourceCompileError("prebreakout_real_source_market_session_missing")
        if session in session_spine:
            raise RealSourceCompileError("prebreakout_real_source_market_session_duplicate")
        session_spine.append(session)

        rows_this_part = 0
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows_this_part += 1
                market_rows += 1
                company = str(row.get("SP_ENTITY_ID") or "").strip()
                ciq = str(row.get("SP_CIQ_ID") or "").strip()
                trading = str(row.get("SP_TRADING_ITEM_ID") or "").strip()
                if not company.isdigit() or not re.fullmatch(r"IQ\d+", ciq) or not trading.isdigit():
                    raise RealSourceCompileError("prebreakout_real_source_market_identity_invalid")
                company_ids.add(company)
                listing_ids.add((ciq, trading))
                missing_close += not str(row.get("SP_PRICE_CLOSE") or "").strip()
                missing_total_return += not str(row.get("SP_TOTAL_RETURN") or "").strip()
                missing_volume += not str(row.get("SP_VOLUME") or "").strip()
        if rows_this_part != int(receipt.get("source_security_row_count", -1)):
            raise RealSourceCompileError("prebreakout_real_source_market_row_count_receipt_mismatch")
        market_parts.append(
            {
                "session_date": session,
                "csv_path": csv_path.as_posix(),
                "csv_sha256": csv_hash,
                "csv_bytes": csv_path.stat().st_size,
                "receipt_path": receipt_path.as_posix(),
                "receipt_sha256": receipt_hash,
                "row_count": rows_this_part,
            }
        )

    session_spine.sort()
    if (
        market_rows != EXPECTED_MARKET_ROW_COUNT
        or len(company_ids) != EXPECTED_COMPANY_COUNT
        or len(listing_ids) != EXPECTED_LISTING_COUNT
        or missing_close != EXPECTED_MISSING_CLOSE
        or missing_total_return != EXPECTED_MISSING_TOTAL_RETURN
        or missing_volume != EXPECTED_MISSING_VOLUME
    ):
        raise RealSourceCompileError("prebreakout_real_source_market_custody_totals_invalid")

    lifecycle_path = Path(lifecycle_dir)
    if not lifecycle_path.is_dir():
        raise FileNotFoundError(lifecycle_path)
    lifecycle_files = sorted(lifecycle_path.glob("part_*.csv"))
    if len(lifecycle_files) != EXPECTED_LIFECYCLE_PART_COUNT:
        raise RealSourceCompileError("prebreakout_real_source_lifecycle_part_count_invalid")
    lifecycle_rows = 0
    requested_ids: list[str] = []
    lifecycle_parts: list[dict[str, Any]] = []
    retrieved_at_values: list[str] = []
    for csv_path in lifecycle_files:
        receipt_path = csv_path.with_suffix(".receipt.json")
        if not receipt_path.is_file():
            raise FileNotFoundError(receipt_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        csv_hash = sha256_file(csv_path)
        receipt_hash = sha256_file(receipt_path)
        if receipt.get("raw_object_sha256") != csv_hash:
            raise RealSourceCompileError("prebreakout_real_source_lifecycle_raw_hash_mismatch")
        if receipt.get("w2_contract_sha256") != W2_CONTRACT_SHA256:
            raise RealSourceCompileError("prebreakout_real_source_lifecycle_w2_hash_mismatch")
        if receipt.get("current_profile_state_used") is not False:
            raise RealSourceCompileError("prebreakout_real_source_lifecycle_current_state_forbidden")
        batch = [str(value) for value in receipt.get("requested_entity_ids") or []]
        if len(batch) != int(receipt.get("requested_entity_count", -1)):
            raise RealSourceCompileError("prebreakout_real_source_lifecycle_requested_count_invalid")
        batch_set = set(batch)
        requested_ids.extend(batch)
        retrieved_at_values.append(str(receipt.get("retrieved_at") or ""))
        rows_this_part = 0
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows_this_part += 1
                entity = str(row.get("SP_ENTITY_ID") or "").strip()
                if entity not in batch_set:
                    raise RealSourceCompileError("prebreakout_real_source_lifecycle_entity_outside_batch")
        lifecycle_rows += rows_this_part
        if rows_this_part != int(receipt.get("normalized_entity_event_rows", -1)):
            raise RealSourceCompileError("prebreakout_real_source_lifecycle_row_count_receipt_mismatch")
        lifecycle_parts.append(
            {
                "csv_path": csv_path.as_posix(),
                "csv_sha256": csv_hash,
                "csv_bytes": csv_path.stat().st_size,
                "receipt_path": receipt_path.as_posix(),
                "receipt_sha256": receipt_hash,
                "requested_entity_count": len(batch),
                "row_count": rows_this_part,
            }
        )
    if lifecycle_rows != EXPECTED_LIFECYCLE_ROW_COUNT:
        raise RealSourceCompileError("prebreakout_real_source_lifecycle_row_total_invalid")
    if len(requested_ids) != EXPECTED_COMPANY_COUNT or len(set(requested_ids)) != EXPECTED_COMPANY_COUNT:
        raise RealSourceCompileError("prebreakout_real_source_lifecycle_entity_union_invalid")
    if set(requested_ids) != company_ids:
        raise RealSourceCompileError("prebreakout_real_source_market_lifecycle_entity_union_mismatch")

    partition = freeze_session_partition(session_spine)
    body: dict[str, Any] = {
        "schema_version": REAL_SOURCE_MANIFEST_SCHEMA,
        "compiler_id": REAL_SOURCE_COMPILER_ID,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "market": {
            "session_count": len(session_spine),
            "first_session": session_spine[0],
            "last_session": session_spine[-1],
            "row_count": market_rows,
            "company_count": len(company_ids),
            "exact_listing_count": len(listing_ids),
            "missing_close_count": missing_close,
            "missing_total_return_count": missing_total_return,
            "missing_volume_count": missing_volume,
            "parts": market_parts,
        },
        "lifecycle": {
            "part_count": len(lifecycle_parts),
            "row_count": lifecycle_rows,
            "requested_entity_count": len(requested_ids),
            "requested_entity_union_sha256": hashlib.sha256(
                json.dumps(sorted(requested_ids, key=int), separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "parts": lifecycle_parts,
            "max_retrieved_at": max(retrieved_at_values),
        },
        "session_spine": session_spine,
        "session_partition_sha256": partition["partition_sha256"],
        "current_survivor_back_projection_used": False,
        "current_primary_back_projection_used": False,
        "alternate_listing_backfill_used": False,
        "ticker_identity_fallback_used": False,
        "company_entity_identity_fallback_used": False,
        "permno_fallback_used": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {**body, "manifest_sha256": canonical_sha256(body)}


def collect_entity_tickers(market_parts: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    tickers: dict[str, set[str]] = {}
    for part in market_parts:
        path = Path(str(part["csv_path"]))
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                entity = str(row.get("SP_ENTITY_ID") or "").strip()
                ticker = str(row.get("TICKER") or "").strip().upper()
                if entity and ticker:
                    tickers.setdefault(entity, set()).add(ticker)
    return {entity: tuple(sorted(values)) for entity, values in tickers.items()}


def load_lifecycle_rows(lifecycle_parts: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for part in lifecycle_parts:
        path = Path(str(part["csv_path"]))
        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                row = {key: str(value or "").strip() for key, value in raw.items()}
                if not row.get("SP_ENTITY_ID", "").isdigit():
                    raise RealSourceCompileError("prebreakout_real_source_lifecycle_entity_invalid")
                try:
                    normalized_date = date.fromisoformat(row.get("EVENT_DATE", "")).isoformat()
                except ValueError as exc:
                    raise RealSourceCompileError("prebreakout_real_source_lifecycle_event_date_invalid") from exc
                row["EVENT_DATE"] = normalized_date
                rows.append(row)
    rows.sort(key=lambda row: (row["EVENT_DATE"], int(row["SP_ENTITY_ID"]), row.get("EVENT_OID", "")))
    return rows


def _ticker_anchor_regex(ticker: str) -> re.Pattern[str]:
    escaped = re.escape(ticker)
    return re.compile(rf"\((?:[^():]{{1,24}}):\s*{escaped}\)", re.IGNORECASE)


def resolve_mna_role(headline: str, entity_tickers: Sequence[str]) -> str:
    """Resolve candidate role from a CIQ headline without using ticker as identity."""

    text = " ".join(str(headline or "").split())
    if not text or not entity_tickers:
        return "AMBIGUOUS_ROLE"

    roles: set[str] = set()
    for ticker in entity_tickers:
        for anchor in _ticker_anchor_regex(ticker).finditer(text):
            left = text[max(0, anchor.start() - 220) : anchor.start()]
            right = text[anchor.end() : min(len(text), anchor.end() + 220)]

            if re.search(r"\bfrom\b.{0,180}$", left, re.IGNORECASE):
                roles.add("SELLER_OR_DIVESTOR")
                continue
            if _MNA_TARGET_AFTER_ANCHOR_RE.search(right[:140]):
                roles.add("WHOLE_COMPANY_TARGET")
                continue

            verbs = list(_MNA_VERB_RE.finditer(left))
            if verbs:
                verb = verbs[-1]
                between = left[verb.end() :]
                if not re.search(r"\bfrom\b", between, re.IGNORECASE):
                    if _NONTERMINAL_TARGET_OBJECT_RE.search(between):
                        roles.add("NONTERMINAL_TARGET_OBJECT")
                    else:
                        roles.add("WHOLE_COMPANY_TARGET")
                    continue

            if _MNA_ACQUIRER_AFTER_ANCHOR_RE.search(right[:180]):
                roles.add("ACQUIRER")
                continue

    if "WHOLE_COMPANY_TARGET" in roles:
        if roles - {"WHOLE_COMPANY_TARGET", "NONTERMINAL_TARGET_OBJECT"}:
            return "AMBIGUOUS_ROLE"
        return "WHOLE_COMPANY_TARGET"
    if roles and roles.issubset({"ACQUIRER", "SELLER_OR_DIVESTOR", "NONTERMINAL_TARGET_OBJECT"}):
        return "NONTERMINAL_COUNTERPARTY_OR_PARTIAL"
    return "AMBIGUOUS_ROLE"


def classify_delisting_event(headline: str, description: str = "") -> str:
    text = " ".join(f"{headline} {description}".split())
    if _DELIST_NONTERMINAL_RE.search(text):
        return "NONTERMINAL_LISTING_ADMIN"
    if _DELIST_PENDING_RE.search(text):
        return "POTENTIAL_TERMINAL_UNRESOLVED"
    if _DELIST_EFFECTIVE_RE.search(text):
        return "TERMINAL_EFFECTIVE"
    return "POTENTIAL_TERMINAL_UNRESOLVED"


def _first_session_strictly_after(event_date: str, sessions: Sequence[str]) -> str | None:
    if event_date < sessions[0]:
        return None
    for session in sessions:
        if session > event_date:
            return session
    return None


def classify_lifecycle_transition(
    row: Mapping[str, str],
    *,
    entity_tickers: Sequence[str],
    session_spine: Sequence[str],
) -> LifecycleTransition | None:
    entity = str(row.get("SP_ENTITY_ID") or "")
    event_date = str(row.get("EVENT_DATE") or "")
    raw_type = str(row.get("EVENT_TYPE") or "")
    headline = str(row.get("HEADLINE") or "")
    description = str(row.get("DESCRIPTION") or "")
    oid = str(row.get("EVENT_OID") or "")
    activation = _first_session_strictly_after(event_date, session_spine)
    if activation is None:
        return None

    type_parts = {part.strip() for part in raw_type.split(",") if part.strip()}
    role = "NOT_APPLICABLE"
    kind = "NOOP"
    state_event_type = "NONE"

    if MNA_CLOSING in type_parts or MNA_ANNOUNCEMENT in type_parts or MNA_CANCELLATION in type_parts:
        role = resolve_mna_role(headline, entity_tickers)
        if MNA_CLOSING in type_parts:
            if role == "WHOLE_COMPANY_TARGET":
                kind = "SET_EFFECTIVE"
                state_event_type = "CIQ_MNA_TARGET_CLOSING"
            elif role == "AMBIGUOUS_ROLE":
                kind = "SET_UNRESOLVED"
                state_event_type = "CIQ_MNA_CLOSING_ROLE_UNRESOLVED"
        elif MNA_CANCELLATION in type_parts:
            if role == "WHOLE_COMPANY_TARGET":
                kind = "CLEAR_IF_MNA_UNRESOLVED"
                state_event_type = "CIQ_MNA_TARGET_CANCELLATION"
        elif role == "WHOLE_COMPANY_TARGET":
            kind = "SET_UNRESOLVED"
            state_event_type = "CIQ_MNA_TARGET_ANNOUNCEMENT_UNRESOLVED"
        elif role == "AMBIGUOUS_ROLE":
            kind = "SET_UNRESOLVED"
            state_event_type = "CIQ_MNA_ANNOUNCEMENT_ROLE_UNRESOLVED"

    elif DELISTING in type_parts:
        role = classify_delisting_event(headline, description)
        if role == "TERMINAL_EFFECTIVE":
            kind = "SET_EFFECTIVE"
            state_event_type = "CIQ_DELISTING_EFFECTIVE"
        elif role == "POTENTIAL_TERMINAL_UNRESOLVED":
            kind = "SET_UNRESOLVED"
            state_event_type = "CIQ_DELISTING_UNRESOLVED"
        else:
            kind = "CLEAR_IF_DELISTING_UNRESOLVED"
            state_event_type = "CIQ_DELISTING_ADMIN_CLEAR"

    elif BANKRUPTCY_FILING in type_parts or BANKRUPTCY_LIQUIDATION in type_parts:
        role = "BANKRUPTCY_TERMINALITY_UNRESOLVED"
        kind = "SET_UNRESOLVED"
        state_event_type = "CIQ_BANKRUPTCY_TERMINALITY_UNRESOLVED"
    elif BANKRUPTCY_EMERGENCE in type_parts or BANKRUPTCY_CONCLUSION in type_parts:
        role = "BANKRUPTCY_EXIT_OR_CONCLUSION"
        kind = "CLEAR_IF_BANKRUPTCY_UNRESOLVED"
        state_event_type = "CIQ_BANKRUPTCY_EXIT_OR_CONCLUSION"
    elif STOCK_SPLIT in type_parts or TICKER_CHANGE in type_parts or EXCHANGE_CHANGE in type_parts:
        role = "NONTERMINAL_AUDIT_EVENT"
    elif any(part.startswith("Bankruptcy:") for part in type_parts):
        role = "BANKRUPTCY_CONTEXT_ONLY"

    if kind == "NOOP":
        return None
    return LifecycleTransition(
        entity_id=entity,
        source_event_date=event_date,
        activation_session=activation,
        transition_kind=kind,
        state_event_type=state_event_type,
        event_oid=oid,
        raw_event_type=raw_type,
        role_resolution=role,
        headline=headline,
    )


def build_lifecycle_transitions(
    *,
    lifecycle_rows: Sequence[Mapping[str, str]],
    entity_tickers: Mapping[str, Sequence[str]],
    session_spine: Sequence[str],
) -> dict[str, list[LifecycleTransition]]:
    transitions: dict[str, list[LifecycleTransition]] = {}
    for row in lifecycle_rows:
        entity = str(row.get("SP_ENTITY_ID") or "")
        transition = classify_lifecycle_transition(
            row,
            entity_tickers=entity_tickers.get(entity, ()),
            session_spine=session_spine,
        )
        if transition is not None:
            transitions.setdefault(transition.activation_session, []).append(transition)
    for session in transitions:
        transitions[session].sort(
            key=lambda value: (
                int(value.entity_id),
                value.source_event_date,
                _EVENT_PRIORITY[value.transition_kind],
                value.event_oid,
            )
        )
    return transitions


def apply_lifecycle_transition(state: LifecycleState, transition: LifecycleTransition) -> LifecycleState:
    kind = transition.transition_kind
    if kind == "SET_EFFECTIVE":
        return LifecycleState(
            action_state=ACTION_EFFECTIVE_TERMINAL,
            effective_session_date=transition.activation_session,
            event_type=transition.state_event_type,
            source_event_date=transition.source_event_date,
            event_oid=transition.event_oid,
            role_resolution=transition.role_resolution,
        )
    if state.action_state == ACTION_EFFECTIVE_TERMINAL:
        return state
    if kind == "SET_UNRESOLVED":
        return LifecycleState(
            action_state=ACTION_UNRESOLVED,
            effective_session_date=None,
            event_type=transition.state_event_type,
            source_event_date=transition.source_event_date,
            event_oid=transition.event_oid,
            role_resolution=transition.role_resolution,
        )
    if kind == "CLEAR_IF_MNA_UNRESOLVED" and state.event_type.startswith("CIQ_MNA_"):
        return LifecycleState()
    if kind == "CLEAR_IF_DELISTING_UNRESOLVED" and state.event_type.startswith("CIQ_DELISTING_"):
        return LifecycleState()
    if kind == "CLEAR_IF_BANKRUPTCY_UNRESOLVED" and state.event_type.startswith("CIQ_BANKRUPTCY_"):
        return LifecycleState()
    return state


def candidate_rows_from_market(
    market_csv: str | Path,
    *,
    market_receipt_sha256: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(market_csv).open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            primary_raw = str(raw.get("PRIMARY_LISTING_STATE") or "")
            proof_raw = str(raw.get("PRIMARY_LISTING_PROOF_KIND") or "")
            if primary_raw == "PRIMARY_DATE_LOCAL" and proof_raw == "UNIQUE_DATE_LOCAL_QUALIFYING_LISTING":
                primary_state = PRIMARY_DATE_LOCAL
                primary_proof = PRIMARY_PROOF_UNIQUE
            elif primary_raw == "AMBIGUOUS_DATE_LOCAL" and proof_raw == "DATE_LOCAL_AMBIGUOUS_MULTIPLE":
                primary_state = AMBIGUOUS_DATE_LOCAL
                primary_proof = PRIMARY_PROOF_AMBIGUOUS
            else:
                raise RealSourceCompileError("prebreakout_real_source_primary_state_unrecognized")
            trading = str(raw.get("SP_TRADING_ITEM_ID") or "").strip()
            rows.append(
                {
                    "schema_version": CANDIDATE_ROW_SCHEMA,
                    "security_id": "CIQSEC:" + str(raw.get("SP_CIQ_ID") or "").strip(),
                    "company_id": str(raw.get("SP_ENTITY_ID") or "").strip(),
                    "trading_item_id": trading,
                    "spt_instrument_item_id": "SPT" + trading,
                    "membership_as_of_date": str(raw.get("MEMBERSHIP_AS_OF_DATE") or "").strip(),
                    "listing_country": str(raw.get("LISTING_COUNTRY") or "").strip(),
                    "security_class": str(raw.get("SECURITY_CLASS") or "").strip(),
                    "primary_listing_state": primary_state,
                    "primary_listing_proof_kind": primary_proof,
                    "active_tradable": str(raw.get("TRADING_STATUS") or "") == "ACTIVE_TRADABLE",
                    "observed_at": str(raw.get("OBSERVED_AT") or "").strip(),
                    "available_at": str(raw.get("AVAILABLE_AT") or "").strip(),
                    "source_id": MARKET_SOURCE_ID,
                    "source_receipt_sha256": market_receipt_sha256,
                    "identity_receipt_sha256": market_receipt_sha256,
                }
            )
    return rows


def corporate_action_rows_for_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    states: Mapping[str, LifecycleState],
    lifecycle_receipt_sha256: str,
    as_of: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        state = states.get(str(candidate["company_id"]), LifecycleState())
        rows.append(
            {
                "schema_version": CORPORATE_ACTION_ROW_SCHEMA,
                "security_id": str(candidate["security_id"]),
                "trading_item_id": str(candidate["trading_item_id"]),
                "action_state": state.action_state,
                "effective_session_date": state.effective_session_date,
                "event_type": state.event_type,
                "observed_at": as_of,
                "available_at": as_of,
                "source_id": LIFECYCLE_SOURCE_ID,
                "source_receipt_sha256": lifecycle_receipt_sha256,
            }
        )
    return rows


def normalized_market_receipt_binding(
    *,
    market_part: Mapping[str, Any],
    compiler_sha256: str,
) -> dict[str, Any]:
    raw_receipt_path = Path(str(market_part["receipt_path"]))
    receipt = json.loads(raw_receipt_path.read_text(encoding="utf-8-sig"))
    return {
        "source_id": MARKET_SOURCE_ID,
        "provider": PROVIDER,
        "retrieved_at": str(receipt["retrieved_at"]),
        "observed_range_start": str(receipt["session_date"]),
        "observed_range_end": str(receipt["session_date"]),
        "raw_receipt_path": raw_receipt_path.as_posix(),
        "raw_receipt_sha256": str(market_part["receipt_sha256"]),
        "parser_id": REAL_SOURCE_COMPILER_ID,
        "parser_sha256": compiler_sha256,
        "license_scope": str(receipt.get("license_scope") or LICENSE_SCOPE),
        "retention_class": str(receipt.get("retention_class") or RETENTION_CLASS),
    }


def lifecycle_state_receipt_body(
    *,
    decision_session_date: str,
    custody_manifest_sha256: str,
    active_states: Mapping[str, LifecycleState],
    applied_transitions: Sequence[LifecycleTransition],
    compiler_sha256: str,
    raw_lifecycle_retrieved_at: str,
) -> dict[str, Any]:
    nonclear = {
        entity: state.as_dict()
        for entity, state in sorted(active_states.items(), key=lambda item: int(item[0]))
        if state.action_state != ACTION_CLEAR
    }
    body = {
        "schema_version": LIFECYCLE_STATE_RECEIPT_SCHEMA,
        "compiler_id": REAL_SOURCE_COMPILER_ID,
        "compiler_sha256": compiler_sha256,
        "family_id": FAMILY_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "decision_session_date": decision_session_date,
        "source_custody_manifest_sha256": custody_manifest_sha256,
        "lifecycle_baseline": "FIRST_CAPTURED_DATE_LOCAL_ACTIVE_LISTING_OVERRIDES_PRE_CORPUS_EVENT_HISTORY",
        "same_day_event_use": "FORBIDDEN_FIRST_CAPTURED_SESSION_STRICTLY_AFTER_EVENT_DATE",
        "mna_role_resolution": "SOURCE_CAPTURED_TICKER_TEXT_ROLE_CLUE_ONLY_NO_IDENTITY_FALLBACK",
        "ambiguous_potential_terminal_policy": "UNRESOLVED_EXCLUDE_NO_RESCUE",
        "nonclear_entity_state_count": len(nonclear),
        "nonclear_entity_state_sha256": canonical_sha256(nonclear),
        "transitions_activated_on_session": [value.as_dict() for value in applied_transitions],
        "raw_lifecycle_retrieved_at": raw_lifecycle_retrieved_at,
        "current_profile_state_used": False,
        "current_primary_state_used": False,
        "ticker_identity_fallback_used": False,
        "company_entity_identity_fallback_used": False,
        "permno_fallback_used": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return body


def normalized_lifecycle_receipt_binding(
    *,
    receipt_path: str | Path,
    receipt_sha256: str,
    observed_range_start: str,
    observed_range_end: str,
    compiler_sha256: str,
    raw_lifecycle_retrieved_at: str,
) -> dict[str, Any]:
    return {
        "source_id": LIFECYCLE_SOURCE_ID,
        "provider": PROVIDER,
        "retrieved_at": raw_lifecycle_retrieved_at,
        "observed_range_start": observed_range_start,
        "observed_range_end": observed_range_end,
        "raw_receipt_path": Path(receipt_path).as_posix(),
        "raw_receipt_sha256": receipt_sha256,
        "parser_id": REAL_SOURCE_COMPILER_ID,
        "parser_sha256": compiler_sha256,
        "license_scope": LICENSE_SCOPE,
        "retention_class": RETENTION_CLASS,
    }


def source_authority_for_session(
    *,
    decision_session_date: str,
    source_receipt_sha256s: Iterable[str],
) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_AUTHORITY_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "capture_mode": HISTORICAL_CAPTURE_MODE,
        "decision_session_date": decision_session_date,
        "provider": PROVIDER,
        "date_local_membership_query": True,
        "source_population_complete": True,
        "historical_as_of_mechanically_bound": True,
        "corporate_action_coverage_complete": True,
        "current_survivor_back_projection_used": False,
        "current_primary_back_projection_used": False,
        "alternate_listing_backfill_used": False,
        "ticker_fallback_used": False,
        "company_entity_fallback_used": False,
        "permno_fallback_used": False,
        "primary_listing_resolution": "DATE_LOCAL_PROVIDER_OR_UNIQUE_QUALIFYING_LISTING",
        "ambiguous_listing_policy": "DETERMINISTIC_EXCLUDE_NO_FALLBACK",
        "source_receipt_sha256s": sorted(str(value) for value in source_receipt_sha256s),
    }


__all__ = [
    "EXPECTED_SESSION_COUNT",
    "FAMILY_ID",
    "LIFECYCLE_STATE_RECEIPT_SCHEMA",
    "LifecycleState",
    "LifecycleTransition",
    "REAL_SOURCE_COMPILER_ID",
    "REAL_SOURCE_MANIFEST_SCHEMA",
    "RealSourceCompileError",
    "apply_lifecycle_transition",
    "build_lifecycle_transitions",
    "candidate_rows_from_market",
    "canonical_json_bytes",
    "canonical_sha256",
    "classify_delisting_event",
    "classify_lifecycle_transition",
    "collect_entity_tickers",
    "corporate_action_rows_for_candidates",
    "freeze_session_partition",
    "lifecycle_state_receipt_body",
    "load_lifecycle_rows",
    "normalized_lifecycle_receipt_binding",
    "normalized_market_receipt_binding",
    "resolve_mna_role",
    "sha256_file",
    "source_authority_for_session",
    "verify_and_build_custody_manifest",
]
