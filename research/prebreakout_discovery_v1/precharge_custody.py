"""Hash-only Trial-1 pre-charge custody for PREBREAKOUT_DISCOVERY_v1.

This module prepares deterministic source/code identities before Trial #1 is
opened.  It deliberately does not persist or print discovery label values.
Development labels and W2 breakout-episode anchors are computed only to content
hashes; the exact payloads must be recomputed and hash-verified after the trial
is charged before any result-bearing W4/W5 join.

W6 lockbox decisions and the lockbox label-maturity tail are outside this
module's admissible source slice.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import duckdb

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1 import trial1_m0
from research.prebreakout_pit_v1.real_source import canonical_json_bytes, canonical_sha256, sha256_file


PRECHARGE_SCHEMA = "prebreakout_trial1_m0_precharge_custody_v1"
LABEL_CUSTODY_SCHEMA = "prebreakout_w4_development_label_hash_custody_v1"
EPISODE_CUSTODY_SCHEMA = "prebreakout_w4_episode_anchor_hash_custody_v1"
CODE_BUNDLE_SCHEMA = "prebreakout_trial1_m0_code_bundle_v1"
SOURCE_RECEIPT_BUNDLE_SCHEMA = "prebreakout_trial1_m0_source_receipt_bundle_v1"

LABEL_HASH_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:W4_DEVELOPMENT_LABEL_HASH_CUSTODY_V1"
EPISODE_HASH_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:W4_EPISODE_ANCHOR_HASH_CUSTODY_V1"
CODE_BUNDLE_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_CODE_BUNDLE_V1"
DECISION_SPINE_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_DECISION_SPINE_V1"
SOURCE_RECEIPT_BUNDLE_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_SOURCE_RECEIPT_BUNDLE_V1"
EPISODE_ID_DOMAIN = "PREBREAKOUT_DISCOVERY_V1:EFFECTIVE_BREAKOUT_EPISODE_V1"

PRIMARY_HORIZON = w2.PRIMARY_HORIZON_SESSIONS
WINNER_FRACTION = w2.WINNER_FRACTION
BREAKOUT_LOOKBACK = w2.BREAKOUT_LOOKBACK_SESSIONS
BREAKOUT_COOLDOWN = w2.BREAKOUT_EPISODE_COOLDOWN_SESSIONS

CODE_BUNDLE_PATHS = (
    "research/prebreakout_discovery_v1/trial1_m0.py",
    "research/prebreakout_discovery_v1/contracts.py",
    "research/prebreakout_discovery_v1/walk_forward.py",
    "research/prebreakout_discovery_v1/preregistration.py",
)


class PrechargeCustodyError(ValueError):
    """Fail-closed pre-charge custody violation."""


@dataclass(frozen=True)
class HashOnlyCustody:
    schema_version: str
    payload_sha256: str
    record_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "payload_sha256": self.payload_sha256,
            "record_count": self.record_count,
            "payload_persisted": False,
            "payload_values_printed": False,
        }


def stream_record_hash(domain: str, records: Iterable[Mapping[str, Any]]) -> tuple[str, int]:
    """Hash canonical ordered records without retaining the payload."""

    if not str(domain).strip() or "\n" in str(domain):
        raise PrechargeCustodyError("precharge_stream_hash_domain_invalid")
    digest = hashlib.sha256()
    digest.update(str(domain).encode("utf-8"))
    digest.update(b"\n")
    count = 0
    for record in records:
        if not isinstance(record, Mapping):
            raise PrechargeCustodyError("precharge_stream_hash_record_mapping_required")
        digest.update(canonical_json_bytes(dict(record)))
        digest.update(b"\n")
        count += 1
    if count == 0:
        raise PrechargeCustodyError("precharge_stream_hash_records_required")
    return digest.hexdigest(), count


def build_code_bundle_manifest(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    files: list[dict[str, str]] = []
    for relative in CODE_BUNDLE_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        files.append({"path": relative, "sha256": sha256_file(path)})
    body = {
        "schema_version": CODE_BUNDLE_SCHEMA,
        "family_id": w2.FAMILY_ID,
        "trial_id": trial1_m0.TRIAL_ID,
        "implementation_id": trial1_m0.IMPLEMENTATION_ID,
        "files": files,
        "scientific_change_authorized": False,
    }
    return {
        **body,
        "code_bundle_sha256": domain_hash(CODE_BUNDLE_DOMAIN, w2.hash_safe(body)),
    }


def create_market_table(
    connection: duckdb.DuckDBPyConnection,
    *,
    csv_paths: Sequence[str],
    maximum_session_date: str,
) -> int:
    """Create the bounded pre-charge market table, excluding W6 by date."""

    if not csv_paths:
        raise PrechargeCustodyError("precharge_market_csv_paths_required")
    try:
        maximum = date.fromisoformat(maximum_session_date)
    except ValueError as exc:
        raise PrechargeCustodyError("precharge_market_maximum_session_date_invalid") from exc
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE pb_market AS
        WITH source AS (
            SELECT
                'CIQSEC:' || TRIM(SP_CIQ_ID) AS security_id,
                TRIM(SP_TRADING_ITEM_ID) AS trading_item_id,
                CAST(MEMBERSHIP_AS_OF_DATE AS DATE) AS session_date,
                TRY_CAST(NULLIF(TRIM(SP_PRICE_CLOSE), '') AS DOUBLE) AS close,
                TRY_CAST(NULLIF(TRIM(SP_TOTAL_RETURN), '') AS DOUBLE) AS total_return_pct
            FROM read_csv_auto(?, all_varchar=true, union_by_name=true)
            WHERE CAST(MEMBERSHIP_AS_OF_DATE AS DATE) <= CAST(? AS DATE)
        ), normalized AS (
            SELECT
                security_id,
                trading_item_id,
                session_date,
                close,
                CASE
                    WHEN total_return_pct IS NULL OR NOT isfinite(total_return_pct) OR total_return_pct <= -100.0
                    THEN NULL
                    ELSE total_return_pct / 100.0
                END AS total_return_1d
            FROM source
        )
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY security_id, trading_item_id
                ORDER BY session_date
            ) - 1 AS listing_session_ordinal
        FROM normalized
        ORDER BY security_id, trading_item_id, session_date
        """,
        [list(csv_paths), maximum.isoformat()],
    )
    row_count = int(connection.execute("SELECT COUNT(*) FROM pb_market").fetchone()[0])
    if row_count < 1:
        raise PrechargeCustodyError("precharge_market_table_empty")
    invalid = int(
        connection.execute(
            """
            SELECT COUNT(*) FROM pb_market
            WHERE security_id !~ '^CIQSEC:IQ[0-9]+$'
               OR trading_item_id !~ '^[0-9]+$'
               OR close IS NULL OR NOT isfinite(close) OR close <= 0
            """
        ).fetchone()[0]
    )
    if invalid:
        raise PrechargeCustodyError("precharge_market_identity_or_close_invalid")
    duplicate = int(
        connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT security_id, trading_item_id, session_date, COUNT(*) AS n
                FROM pb_market GROUP BY 1,2,3 HAVING COUNT(*) != 1
            )
            """
        ).fetchone()[0]
    )
    if duplicate:
        raise PrechargeCustodyError("precharge_market_exact_listing_session_duplicate")
    return row_count


def iter_development_label_records(
    connection: duckdb.DuckDBPyConnection,
    *,
    decision_dates: Sequence[str],
    candidate_counts: Mapping[str, int],
) -> Iterator[dict[str, Any]]:
    """Yield canonical development label records in deterministic order."""

    dates = [str(value) for value in decision_dates]
    if len(dates) != 226 or len(set(dates)) != len(dates):
        raise PrechargeCustodyError("precharge_development_decision_spine_must_be_226_unique")
    if set(dates) != set(candidate_counts):
        raise PrechargeCustodyError("precharge_candidate_count_date_set_mismatch")

    connection.execute("CREATE OR REPLACE TEMP TABLE pb_candidate_counts(decision_session_date DATE, candidate_count BIGINT)")
    connection.executemany(
        "INSERT INTO pb_candidate_counts VALUES (?, ?)",
        [(value, int(candidate_counts[value])) for value in dates],
    )
    connection.execute("CREATE OR REPLACE TEMP TABLE pb_dev_dates(decision_session_date DATE)")
    connection.executemany("INSERT INTO pb_dev_dates VALUES (?)", [(value,) for value in dates])

    observed = {
        str(row[0]): int(row[1])
        for row in connection.execute(
            """
            SELECT CAST(m.session_date AS VARCHAR), COUNT(*)
            FROM pb_market m
            JOIN pb_dev_dates d ON d.decision_session_date = m.session_date
            GROUP BY 1
            """
        ).fetchall()
    }
    if observed != {key: int(value) for key, value in candidate_counts.items()}:
        raise PrechargeCustodyError("precharge_development_market_population_not_exact_w3_candidate_count")

    query = connection.execute(
        f"""
        WITH forward_windows AS (
            SELECT
                security_id,
                trading_item_id,
                session_date,
                listing_session_ordinal,
                COUNT(*) OVER w AS future_observed_rows,
                COUNT(total_return_1d) OVER w AS future_return_rows,
                SUM(
                    CASE WHEN total_return_1d IS NOT NULL THEN LN(1.0 + total_return_1d) END
                ) OVER w AS future_log_return,
                LEAD(session_date, {PRIMARY_HORIZON}) OVER (
                    PARTITION BY security_id, trading_item_id
                    ORDER BY session_date
                ) AS label_available_date
            FROM pb_market
            WINDOW w AS (
                PARTITION BY security_id, trading_item_id
                ORDER BY session_date
                ROWS BETWEEN 1 FOLLOWING AND {PRIMARY_HORIZON} FOLLOWING
            )
        ), joined AS (
            SELECT
                f.*,
                c.candidate_count,
                CAST(CEIL({WINNER_FRACTION} * c.candidate_count) AS BIGINT) AS required_winner_count,
                CASE
                    WHEN f.future_observed_rows = {PRIMARY_HORIZON}
                     AND f.future_return_rows = {PRIMARY_HORIZON}
                    THEN EXP(f.future_log_return) - 1.0
                    ELSE NULL
                END AS forward_total_return
            FROM forward_windows f
            JOIN pb_dev_dates d ON d.decision_session_date = f.session_date
            JOIN pb_candidate_counts c ON c.decision_session_date = f.session_date
        ), ranked AS (
            SELECT
                *,
                COUNT(forward_total_return) OVER (PARTITION BY session_date) AS matured_count,
                ROW_NUMBER() OVER (
                    PARTITION BY session_date
                    ORDER BY forward_total_return DESC NULLS LAST, security_id ASC, trading_item_id ASC
                ) AS rank_ordinal
            FROM joined
        )
        SELECT
            CAST(session_date AS VARCHAR),
            security_id,
            trading_item_id,
            listing_session_ordinal,
            candidate_count,
            required_winner_count,
            matured_count,
            label_available_date,
            forward_total_return,
            CASE
                WHEN forward_total_return IS NULL THEN NULL
                WHEN rank_ordinal <= required_winner_count THEN TRUE
                ELSE FALSE
            END AS winner_label
        FROM ranked
        ORDER BY session_date, security_id, trading_item_id
        """
    )
    while True:
        batch = query.fetchmany(20_000)
        if not batch:
            break
        for (
            decision_date,
            security_id,
            trading_item_id,
            listing_ordinal,
            candidate_count,
            required_winner_count,
            matured_count,
            label_available_date,
            forward_return,
            winner_label,
        ) in batch:
            if int(matured_count) < int(required_winner_count):
                raise PrechargeCustodyError("precharge_matured_rows_fewer_than_required_winner_count")
            yield {
                "schema_version": LABEL_CUSTODY_SCHEMA,
                "family_id": w2.FAMILY_ID,
                "label_spec_id": w2.PRIMARY_LABEL_SPEC_ID,
                "decision_session_date": str(decision_date),
                "security_id": str(security_id),
                "trading_item_id": str(trading_item_id),
                "listing_session_ordinal": int(listing_ordinal),
                "candidate_count": int(candidate_count),
                "required_winner_count": int(required_winner_count),
                "label_available_date": None if label_available_date is None else str(label_available_date),
                "horizon_status": "INCOMPLETE_HORIZON" if forward_return is None else "MATURED_HASHED_NOT_INSPECTED",
                "forward_total_return": None if forward_return is None else format(float(forward_return), ".17g"),
                "winner_label": None if winner_label is None else bool(winner_label),
            }


def compute_development_label_hash(
    connection: duckdb.DuckDBPyConnection,
    *,
    decision_dates: Sequence[str],
    candidate_counts: Mapping[str, int],
) -> HashOnlyCustody:
    """Compute exact 20-session top-5% labels to a hash only."""

    digest, count = stream_record_hash(
        LABEL_HASH_DOMAIN,
        iter_development_label_records(
            connection,
            decision_dates=decision_dates,
            candidate_counts=candidate_counts,
        ),
    )
    return HashOnlyCustody(LABEL_CUSTODY_SCHEMA, digest, count)


def iter_episode_anchor_records(
    connection: duckdb.DuckDBPyConnection,
    *,
    session_spine: Sequence[str],
    development_decision_dates: Sequence[str],
) -> Iterator[dict[str, Any]]:
    """Yield frozen W2 B/B-1 anchors using exact observed listing ordinals."""

    sessions = [str(value) for value in session_spine]
    global_ordinal = {value: index for index, value in enumerate(sessions)}
    if len(global_ordinal) != len(sessions):
        raise PrechargeCustodyError("precharge_session_spine_duplicate")
    development = set(map(str, development_decision_dates))

    cursor = connection.execute(
        """
        SELECT security_id, trading_item_id, CAST(session_date AS VARCHAR), close, listing_session_ordinal
        FROM pb_market
        ORDER BY security_id, trading_item_id, listing_session_ordinal
        """
    )
    current_key: tuple[str, str] | None = None
    prior: deque[tuple[str, float, int]] = deque(maxlen=BREAKOUT_LOOKBACK)
    prior_session: tuple[str, float, int] | None = None
    last_accepted_listing_ordinal: int | None = None
    while True:
        batch = cursor.fetchmany(20_000)
        if not batch:
            break
        for security_id, trading_item_id, session_date, close, listing_ordinal in batch:
            key = (str(security_id), str(trading_item_id))
            if key != current_key:
                current_key = key
                prior = deque(maxlen=BREAKOUT_LOOKBACK)
                prior_session = None
                last_accepted_listing_ordinal = None
            listing_index = int(listing_ordinal)
            close_value = float(close)
            if len(prior) == BREAKOUT_LOOKBACK:
                prior_high = max(item[1] for item in prior)
                raw_breakout = close_value > prior_high
                cooldown_clear = (
                    last_accepted_listing_ordinal is None
                    or listing_index - last_accepted_listing_ordinal > BREAKOUT_COOLDOWN
                )
                if raw_breakout and cooldown_clear:
                    if prior_session is None:
                        raise PrechargeCustodyError("precharge_breakout_missing_bminus1")
                    b1_date, _, b1_listing_ordinal = prior_session
                    if b1_date in development:
                        if session_date not in global_ordinal or b1_date not in global_ordinal:
                            raise PrechargeCustodyError("precharge_episode_date_absent_from_session_spine")
                        lead_start_date, _, lead_start_listing_ordinal = prior[0]
                        identity = {
                            "security_id": key[0],
                            "trading_item_id": key[1],
                            "breakout_session_date": str(session_date),
                            "breakout_listing_session_ordinal": listing_index,
                        }
                        yield {
                            "schema_version": EPISODE_CUSTODY_SCHEMA,
                            "family_id": w2.FAMILY_ID,
                            "breakout_contract_sha256": w2.CONTRACT_SHA256,
                            "effective_episode_id": domain_hash(EPISODE_ID_DOMAIN, w2.hash_safe(identity)),
                            "security_id": key[0],
                            "trading_item_id": key[1],
                            "breakout_session_date": str(session_date),
                            "breakout_session_ordinal": int(global_ordinal[str(session_date)]),
                            "breakout_listing_session_ordinal": listing_index,
                            "b_minus_1_session_date": b1_date,
                            "b_minus_1_session_ordinal": int(global_ordinal[b1_date]),
                            "b_minus_1_listing_session_ordinal": int(b1_listing_ordinal),
                            "lead_window_start_session_date": lead_start_date,
                            "lead_window_start_session_ordinal": int(global_ordinal[lead_start_date]),
                            "lead_window_start_listing_session_ordinal": int(lead_start_listing_ordinal),
                        }
                    last_accepted_listing_ordinal = listing_index
            prior.append((str(session_date), close_value, listing_index))
            prior_session = (str(session_date), close_value, listing_index)


def compute_episode_anchor_hash(
    connection: duckdb.DuckDBPyConnection,
    *,
    session_spine: Sequence[str],
    development_decision_dates: Sequence[str],
) -> HashOnlyCustody:
    """Hash frozen W2 B/B-1 anchors using exact observed listing ordinals."""

    digest, count = stream_record_hash(
        EPISODE_HASH_DOMAIN,
        iter_episode_anchor_records(
            connection,
            session_spine=session_spine,
            development_decision_dates=development_decision_dates,
        ),
    )
    return HashOnlyCustody(EPISODE_CUSTODY_SCHEMA, digest, count)


def build_trial1_source_manifest(
    *,
    market_history_payload_sha256: str,
    w3_pit_authority_bundle_sha256: str,
    development_label_custody_sha256: str,
    episode_custody_sha256: str,
    decision_spine_sha256: str,
    source_receipt_bundle_sha256: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": trial1_m0.SOURCE_MANIFEST_SCHEMA,
        "family_id": w2.FAMILY_ID,
        "w2_contract_sha256": w2.CONTRACT_SHA256,
        "risk_set_spec_id": w2.RISK_SET_SPEC_ID,
        "primary_label_spec_id": w2.PRIMARY_LABEL_SPEC_ID,
        "market_history_payload_sha256": market_history_payload_sha256,
        "w3_pit_authority_bundle_sha256": w3_pit_authority_bundle_sha256,
        "w4_control_definition_sha256": trial1_m0.TRIAL1_W4_CONTROL_DEFINITION_SHA256,
        "w4_development_label_custody_sha256": development_label_custody_sha256,
        "w4_episode_custody_sha256": episode_custody_sha256,
        "decision_spine_sha256": decision_spine_sha256,
        "source_receipt_bundle_sha256": source_receipt_bundle_sha256,
        "development_label_visibility_at_manifest": "HASHED_NOT_INSPECTED",
        "smoke_statistical_weight": 0,
        "holdout_label_tuning_authority": "FORBIDDEN",
        "w6_lockbox_included": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "authority_class": trial1_m0.SOURCE_AUTHORITY_CLASS,
    }
    manifest = {
        **body,
        "manifest_sha256": domain_hash(
            "PREBREAKOUT_DISCOVERY_V1:TRIAL1_M0_SOURCE_MANIFEST",
            w2.hash_safe(body),
        ),
    }
    trial1_m0.verify_trial1_source_manifest(manifest)
    return manifest


def development_market_payload_hash(market_parts: Sequence[Mapping[str, Any]]) -> str:
    rows = [
        {"session_date": str(part["session_date"]), "csv_sha256": str(part["csv_sha256"])}
        for part in market_parts
    ]
    if not rows:
        raise PrechargeCustodyError("precharge_development_market_parts_required")
    return canonical_sha256(rows)


def development_w3_bundle_hash(authority_entries: Sequence[Mapping[str, Any]]) -> str:
    rows = [
        {
            "decision_session_date": str(entry["decision_session_date"]),
            "authority_packet_sha256": str(entry["authority_packet_sha256"]),
        }
        for entry in authority_entries
    ]
    if not rows:
        raise PrechargeCustodyError("precharge_development_w3_entries_required")
    return canonical_sha256(rows)


def source_receipt_bundle_hash(
    *,
    market_parts: Sequence[Mapping[str, Any]],
    authority_entries: Sequence[Mapping[str, Any]],
) -> str:
    rows: list[dict[str, Any]] = []
    for part in market_parts:
        rows.append(
            {
                "schema_version": SOURCE_RECEIPT_BUNDLE_SCHEMA,
                "role": "MARKET_PART_RECEIPT",
                "session_date": str(part["session_date"]),
                "receipt_sha256": str(part["receipt_sha256"]),
            }
        )
    for entry in authority_entries:
        rows.append(
            {
                "schema_version": SOURCE_RECEIPT_BUNDLE_SCHEMA,
                "role": "W3_LIFECYCLE_STATE_RECEIPT",
                "session_date": str(entry["decision_session_date"]),
                "receipt_sha256": str(entry["lifecycle_state_receipt_sha256"]),
            }
        )
    rows.sort(key=lambda row: (row["role"], row["session_date"], row["receipt_sha256"]))
    return domain_hash(SOURCE_RECEIPT_BUNDLE_DOMAIN, w2.hash_safe(rows))


def decision_spine_hash(decision_dates: Sequence[str]) -> str:
    dates = [str(value) for value in decision_dates]
    if len(dates) != 226 or len(set(dates)) != 226:
        raise PrechargeCustodyError("precharge_decision_spine_invalid")
    return domain_hash(DECISION_SPINE_DOMAIN, w2.hash_safe(dates))


__all__ = [
    "CODE_BUNDLE_PATHS",
    "EPISODE_CUSTODY_SCHEMA",
    "HashOnlyCustody",
    "LABEL_CUSTODY_SCHEMA",
    "PRECHARGE_SCHEMA",
    "PrechargeCustodyError",
    "build_code_bundle_manifest",
    "build_trial1_source_manifest",
    "compute_development_label_hash",
    "compute_episode_anchor_hash",
    "create_market_table",
    "decision_spine_hash",
    "development_market_payload_hash",
    "development_w3_bundle_hash",
    "iter_development_label_records",
    "iter_episode_anchor_records",
    "source_receipt_bundle_hash",
    "stream_record_hash",
]
