from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


class SupercycleDiscoveryTheme(StrEnum):
    AI_COMPUTE_INFRA = "AI_COMPUTE_INFRA"
    AI_SERVER_SUPPLY_CHAIN = "AI_SERVER_SUPPLY_CHAIN"
    MEMORY_STORAGE_SUPERCYCLE = "MEMORY_STORAGE_SUPERCYCLE"
    SEMICAP_EQUIPMENT = "SEMICAP_EQUIPMENT"
    POWER_COOLING_GRID = "POWER_COOLING_GRID"
    CRITICAL_MINERALS_LITHIUM = "CRITICAL_MINERALS_LITHIUM"
    RESHORING_FOUNDRY = "RESHORING_FOUNDRY"
    DEFENSE_INDUSTRIAL = "DEFENSE_INDUSTRIAL"
    BIOTECH_PLATFORM = "BIOTECH_PLATFORM"


class CandidateIntakeStatus(StrEnum):
    INTAKE_ONLY = "intake_only"
    CANDIDATE_CARD_EXISTS = "candidate_card_exists"


class DiscoveryOrigin(StrEnum):
    USER_SEEDED = "USER_SEEDED"
    THEME_ADJACENT = "THEME_ADJACENT"
    SUPPLY_CHAIN_ADJACENT = "SUPPLY_CHAIN_ADJACENT"
    PEER_CLUSTER = "PEER_CLUSTER"
    CUSTOMER_SUPPLIER_LINK = "CUSTOMER_SUPPLIER_LINK"
    ETF_HOLDING_LINK = "ETF_HOLDING_LINK"
    SEC_INDUSTRY_LINK = "SEC_INDUSTRY_LINK"
    NEWS_RESEARCH_CAPTURE = "NEWS_RESEARCH_CAPTURE"
    LOCAL_FACTOR_SCOUT = "LOCAL_FACTOR_SCOUT"
    SYSTEM_SCOUTED = "SYSTEM_SCOUTED"


REQUIRED_THEME_IDS = frozenset(theme.value for theme in SupercycleDiscoveryTheme)
REQUIRED_DISCOVERY_ORIGINS = frozenset(origin.value for origin in DiscoveryOrigin)

REQUIRED_QUEUE_FIELDS = frozenset(
    {
        "queue_id",
        "created_at",
        "scope",
        "authority",
        "candidate_intake_items",
        "forbidden_outputs",
    }
)

EXPECTED_QUEUE_SCOPE = "PH65_G8_1_INTAKE_ONLY"
EXPECTED_QUEUE_AUTHORITY = "candidate_discovery_intake_only"
EXPECTED_MANIFEST_ARTIFACT_URI = "data/discovery/supercycle_candidate_intake_queue_v0.json"

REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "manifest_id",
        "artifact_uri",
        "artifact_sha256",
        "created_at",
        "scope",
        "queue_id",
        "row_count",
        "seed_tickers",
        "status_policy",
        "source_policy",
        "allowed_use",
        "forbidden_use",
    }
)

REQUIRED_INTAKE_ITEM_FIELDS = frozenset(
    {
        "ticker",
        "company_name",
        "theme_candidates",
        "why_it_might_belong",
        "evidence_needed",
        "known_source_candidates",
        "official_sources_needed",
        "market_behavior_modules_relevant",
        "thesis_breakers_to_check",
        "provider_gaps",
        "current_status",
        "discovery_origin",
        "origin_evidence",
        "scout_path",
        "is_user_seeded",
        "is_system_scouted",
        "is_validated",
        "is_actionable",
        "not_alpha_evidence",
        "no_score",
        "no_rank",
        "no_buy_sell_signal",
    }
)

REQUIRED_FORBIDDEN_OUTPUT_FLAGS = {
    "no_score": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_candidate_ranking": True,
    "no_validated_thesis": True,
    "no_buying_range": True,
}

ALLOWED_NEGATED_KEYS = frozenset(
    {
        "no_score",
        "no_rank",
        "no_buy_sell_signal",
        "no_candidate_ranking",
        "no_validated_thesis",
        "no_buying_range",
        "not_alpha_evidence",
    }
)

FORBIDDEN_SCORE_RANK_KEYS = frozenset(
    {
        "score",
        "alpha_score",
        "signal_score",
        "candidate_score",
        "rank",
        "ranking",
        "candidate_rank",
        "rank_position",
        "top_pick",
        "best_candidate",
        "upside",
        "upside_pct",
        "price_target",
        "target_price",
    }
)

FORBIDDEN_ACTION_KEYS = frozenset(
    {
        "buy_sell_signal",
        "buy_signal",
        "sell_signal",
        "hold_signal",
        "trade_signal",
        "recommendation",
        "rating",
        "buy_range",
        "buying_range",
        "entry_price",
        "alert",
        "alert_emitted",
        "broker_action",
        "broker_call",
        "order",
        "order_action",
        "buy_order",
        "sell_order",
    }
)

FORBIDDEN_PROMOTION_KEYS = frozenset(
    {
        "candidate_card_authority",
        "candidate_card_created",
        "candidate_card_promotion",
        "candidate_card_status",
        "full_candidate_card",
        "new_candidate_card",
        "second_candidate_card",
        "promote_to_candidate_card",
        "validated_thesis_status",
    }
)

FORBIDDEN_PROMOTION_TEXT = (
    "candidate card authority",
    "second candidate card",
    "full candidate card",
    "new candidate card",
    "promote to candidate card",
    "promoted to candidate card",
    "validated thesis",
    "buying range",
    "let winner run",
)

FORBIDDEN_PROMOTION_STATES = frozenset(
    {
        "VALIDATED_THESIS",
        "BUYING_RANGE",
        "LET_WINNER_RUN",
        "ADD_ON_SETUP",
        "TRIM_OPTIONAL",
    }
)

REQUIRED_SEED_TICKERS = ("MU", "DELL", "INTC", "AMD", "LRCX", "ALB")


@dataclass(frozen=True)
class DiscoveryIntakeValidationResult:
    valid: bool
    errors: tuple[str, ...]


class DiscoveryIntakeValidationError(ValueError):
    pass


def validate_discovery_theme_taxonomy(themes: Mapping[str, Any]) -> DiscoveryIntakeValidationResult:
    errors: list[str] = []
    theme_items = themes.get("themes")
    if not isinstance(theme_items, list) or not theme_items:
        errors.append("themes must be a non-empty list")
        return DiscoveryIntakeValidationResult(valid=False, errors=tuple(errors))

    observed_theme_ids: set[str] = set()
    for index, theme in enumerate(theme_items):
        if not isinstance(theme, Mapping):
            errors.append(f"themes[{index}] must be an object")
            continue
        theme_id = theme.get("theme_id")
        if theme_id not in REQUIRED_THEME_IDS:
            errors.append(f"unknown theme_id: {theme_id}")
            continue
        observed_theme_ids.add(str(theme_id))
        for field_name in ("label", "description", "evidence_requirements"):
            value = theme.get(field_name)
            if not value:
                errors.append(f"themes[{index}].{field_name} is required")

    missing = sorted(REQUIRED_THEME_IDS.difference(observed_theme_ids))
    if missing:
        errors.append(f"missing required discovery themes: {', '.join(missing)}")

    return DiscoveryIntakeValidationResult(valid=not errors, errors=tuple(errors))


def validate_candidate_intake_queue(
    queue: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> DiscoveryIntakeValidationResult:
    errors: list[str] = []

    _validate_required_queue_fields(queue, errors)
    _validate_forbidden_output_flags(queue, errors)
    _validate_seed_items(queue, errors)
    _validate_no_forbidden_fields(queue, errors)
    _validate_no_promotion_states(queue, errors)
    _validate_no_canonical_sources(queue, manifest, errors)
    _validate_manifest(queue, manifest, errors)

    return DiscoveryIntakeValidationResult(valid=not errors, errors=tuple(errors))


def assert_valid_candidate_intake_queue(
    queue: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
) -> None:
    result = validate_candidate_intake_queue(queue, manifest=manifest)
    if not result.valid:
        raise DiscoveryIntakeValidationError("; ".join(result.errors))


def _validate_required_queue_fields(queue: Mapping[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_QUEUE_FIELDS.difference(queue))
    if missing:
        errors.append(f"missing required queue fields: {', '.join(missing)}")

    if queue.get("scope") != EXPECTED_QUEUE_SCOPE:
        errors.append(f"scope must be {EXPECTED_QUEUE_SCOPE}")
    if queue.get("authority") != EXPECTED_QUEUE_AUTHORITY:
        errors.append(f"authority must be {EXPECTED_QUEUE_AUTHORITY}")

    items = queue.get("candidate_intake_items")
    if not isinstance(items, list) or not items:
        errors.append("candidate_intake_items must be a non-empty list")
        return

    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"candidate_intake_items[{index}] must be an object")
            continue
        _validate_intake_item(index, item, errors)


def _validate_intake_item(index: int, item: Mapping[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_INTAKE_ITEM_FIELDS.difference(item))
    if missing:
        errors.append(f"candidate_intake_items[{index}] missing fields: {', '.join(missing)}")

    ticker = item.get("ticker")
    if not isinstance(ticker, str) or not ticker.strip():
        errors.append(f"candidate_intake_items[{index}].ticker is required")

    theme_candidates = item.get("theme_candidates")
    if not isinstance(theme_candidates, list) or not theme_candidates:
        errors.append(f"candidate_intake_items[{index}].theme_candidates is required")
    else:
        unknown_themes = sorted(str(theme) for theme in theme_candidates if theme not in REQUIRED_THEME_IDS)
        if unknown_themes:
            errors.append(
                f"candidate_intake_items[{index}].theme_candidates has unknown themes: {', '.join(unknown_themes)}"
            )

    for field_name in ("evidence_needed", "thesis_breakers_to_check", "provider_gaps"):
        value = item.get(field_name)
        if not isinstance(value, list) or not value:
            errors.append(f"candidate_intake_items[{index}].{field_name} is required")

    current_status = item.get("current_status")
    allowed_statuses = {status.value for status in CandidateIntakeStatus}
    if current_status not in allowed_statuses:
        errors.append(f"candidate_intake_items[{index}].current_status must be intake_only or candidate_card_exists")

    _validate_origin_fields(index, item, errors)

    for flag_name in ("not_alpha_evidence", "no_score", "no_rank", "no_buy_sell_signal"):
        if item.get(flag_name) is not True:
            errors.append(f"candidate_intake_items[{index}].{flag_name} must be true")


def _validate_origin_fields(index: int, item: Mapping[str, Any], errors: list[str]) -> None:
    raw_origins = item.get("discovery_origin")
    origin_values = _origin_values(raw_origins)
    if not origin_values:
        errors.append(f"candidate_intake_items[{index}].discovery_origin is required")
    else:
        unknown_origins = sorted(origin for origin in origin_values if origin not in REQUIRED_DISCOVERY_ORIGINS)
        if unknown_origins:
            errors.append(
                f"candidate_intake_items[{index}].discovery_origin has unknown origins: {', '.join(unknown_origins)}"
            )

    origin_evidence = item.get("origin_evidence")
    if not isinstance(origin_evidence, list) or not origin_evidence:
        errors.append(f"candidate_intake_items[{index}].origin_evidence is required")

    scout_path = item.get("scout_path")
    if not isinstance(scout_path, list):
        errors.append(f"candidate_intake_items[{index}].scout_path is required")

    for flag_name in ("is_user_seeded", "is_system_scouted", "is_validated", "is_actionable"):
        if not isinstance(item.get(flag_name), bool):
            errors.append(f"candidate_intake_items[{index}].{flag_name} must be boolean")

    is_user_seeded = item.get("is_user_seeded") is True
    is_system_scouted = item.get("is_system_scouted") is True
    is_validated = item.get("is_validated") is True
    is_actionable = item.get("is_actionable") is True

    if DiscoveryOrigin.USER_SEEDED.value in origin_values and not is_user_seeded:
        errors.append(f"candidate_intake_items[{index}].USER_SEEDED origin requires is_user_seeded=true")
    if is_user_seeded and DiscoveryOrigin.USER_SEEDED.value not in origin_values:
        errors.append(f"candidate_intake_items[{index}].is_user_seeded=true requires USER_SEEDED origin")
    if DiscoveryOrigin.SYSTEM_SCOUTED.value in origin_values and not is_system_scouted:
        errors.append(f"candidate_intake_items[{index}].SYSTEM_SCOUTED origin requires is_system_scouted=true")
    if is_system_scouted and DiscoveryOrigin.SYSTEM_SCOUTED.value not in origin_values:
        errors.append(f"candidate_intake_items[{index}].is_system_scouted=true requires SYSTEM_SCOUTED origin")
    if is_user_seeded and is_system_scouted:
        errors.append(f"candidate_intake_items[{index}].user_seeded and system_scouted must remain distinct")
    if is_system_scouted and not scout_path:
        errors.append(f"candidate_intake_items[{index}].scout_path is required for system_scouted")
    if DiscoveryOrigin.LOCAL_FACTOR_SCOUT.value in origin_values:
        errors.append("LOCAL_FACTOR_SCOUT is defined but held until G8.1B")
    if is_validated:
        errors.append(f"candidate_intake_items[{index}].is_validated must be false for discovery intake")
    if is_actionable:
        errors.append(f"candidate_intake_items[{index}].is_actionable must be false for discovery intake")


def _validate_forbidden_output_flags(queue: Mapping[str, Any], errors: list[str]) -> None:
    forbidden_outputs = queue.get("forbidden_outputs")
    if not isinstance(forbidden_outputs, Mapping):
        errors.append("forbidden_outputs is required")
        return

    for field_name, expected_value in REQUIRED_FORBIDDEN_OUTPUT_FLAGS.items():
        if forbidden_outputs.get(field_name) is not expected_value:
            errors.append(f"forbidden_outputs.{field_name} must be true")


def _validate_seed_items(queue: Mapping[str, Any], errors: list[str]) -> None:
    items = queue.get("candidate_intake_items")
    if not isinstance(items, list):
        return

    tickers = [str(item.get("ticker", "")).strip().upper() for item in items if isinstance(item, Mapping)]
    if tuple(tickers) != REQUIRED_SEED_TICKERS:
        errors.append("candidate_intake_items must contain exactly MU, DELL, INTC, AMD, LRCX, ALB in that order")

    card_status_tickers = [
        str(item.get("ticker", "")).strip().upper()
        for item in items
        if isinstance(item, Mapping) and item.get("current_status") == CandidateIntakeStatus.CANDIDATE_CARD_EXISTS.value
    ]
    if card_status_tickers != ["MU"]:
        errors.append("MU must be the only candidate_card_exists item")

    for item in items:
        if not isinstance(item, Mapping):
            continue
        ticker = str(item.get("ticker", "")).strip().upper()
        expected_status = (
            CandidateIntakeStatus.CANDIDATE_CARD_EXISTS.value
            if ticker == "MU"
            else CandidateIntakeStatus.INTAKE_ONLY.value
        )
        if item.get("current_status") != expected_status:
            errors.append(f"{ticker or '<blank>'} current_status must be {expected_status}")
        item_origins = _origin_values(item.get("discovery_origin"))
        if item.get("is_system_scouted") is True or DiscoveryOrigin.SYSTEM_SCOUTED.value in item_origins:
            errors.append(f"{ticker or '<blank>'} must not be SYSTEM_SCOUTED in G8.1A")
        if item.get("is_validated") is not False:
            errors.append(f"{ticker or '<blank>'} is_validated must be false")
        if item.get("is_actionable") is not False:
            errors.append(f"{ticker or '<blank>'} is_actionable must be false")

    origin_map = {
        str(item.get("ticker", "")).strip().upper(): _origin_values(item.get("discovery_origin"))
        for item in items
        if isinstance(item, Mapping)
    }
    expected_origin_map = {
        "MU": [DiscoveryOrigin.USER_SEEDED.value],
        "DELL": [DiscoveryOrigin.USER_SEEDED.value, DiscoveryOrigin.THEME_ADJACENT.value],
        "INTC": [DiscoveryOrigin.USER_SEEDED.value, DiscoveryOrigin.THEME_ADJACENT.value],
        "AMD": [DiscoveryOrigin.USER_SEEDED.value, DiscoveryOrigin.THEME_ADJACENT.value],
        "LRCX": [DiscoveryOrigin.USER_SEEDED.value, DiscoveryOrigin.SUPPLY_CHAIN_ADJACENT.value],
        "ALB": [DiscoveryOrigin.USER_SEEDED.value, DiscoveryOrigin.THEME_ADJACENT.value],
    }
    for ticker, expected_origins in expected_origin_map.items():
        if origin_map.get(ticker) != expected_origins:
            errors.append(f"{ticker} discovery_origin must be {', '.join(expected_origins)}")


def _validate_no_forbidden_fields(obj: Any, errors: list[str]) -> None:
    forbidden_keys = FORBIDDEN_SCORE_RANK_KEYS.union(FORBIDDEN_ACTION_KEYS).union(FORBIDDEN_PROMOTION_KEYS)
    for path, key, value in _walk_mapping_keys(obj):
        normalized = _normalize_key(key)
        if normalized in ALLOWED_NEGATED_KEYS:
            continue
        if normalized in forbidden_keys or _is_forbidden_promotion_key(normalized):
            errors.append(f"forbidden field present at {'.'.join((*path, key))}")
        if isinstance(value, str) and _contains_forbidden_action_call(value):
            errors.append(f"forbidden action call present at {'.'.join((*path, key))}")
        if isinstance(value, str) and _contains_forbidden_promotion_text(value):
            errors.append(f"forbidden promotion wording present at {'.'.join((*path, key))}")


def _validate_no_promotion_states(obj: Any, errors: list[str]) -> None:
    for path, key, value in _walk_mapping_keys(obj):
        normalized = _normalize_key(key)
        if normalized in {"no_buying_range", "no_validated_thesis"}:
            continue
        if isinstance(value, str) and value.strip().upper() in FORBIDDEN_PROMOTION_STATES:
            errors.append(f"forbidden promotion state present at {'.'.join((*path, key))}")


def _validate_no_canonical_sources(
    queue: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    canonical_entries = _canonical_source_entries(queue)
    if manifest is not None:
        canonical_entries.extend(_canonical_source_entries(manifest))

    _validate_no_canonical_true_anywhere(queue, errors)
    if manifest is not None:
        _validate_no_canonical_true_anywhere(manifest, errors)

    for entry in canonical_entries:
        errors.append("canonical sources are not allowed for G8.1 discovery intake")
        if "yfinance" in _stringify(entry).lower():
            errors.append("yfinance cannot be a canonical source for discovery intake")


def _validate_manifest(
    queue: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    if manifest is None:
        errors.append("manifest is required")
        return

    missing = sorted(REQUIRED_MANIFEST_FIELDS.difference(manifest))
    if missing:
        errors.append(f"manifest missing fields: {', '.join(missing)}")

    if not manifest.get("artifact_sha256"):
        errors.append("manifest artifact_sha256 is required")

    if manifest.get("artifact_uri") != EXPECTED_MANIFEST_ARTIFACT_URI:
        errors.append(f"manifest artifact_uri must be {EXPECTED_MANIFEST_ARTIFACT_URI}")
    if manifest.get("scope") != queue.get("scope"):
        errors.append("manifest scope must match queue scope")
    if manifest.get("queue_id") != queue.get("queue_id"):
        errors.append("manifest queue_id must match queue queue_id")

    items = queue.get("candidate_intake_items")
    if isinstance(items, list) and manifest.get("row_count") != len(items):
        errors.append("manifest row_count must match candidate_intake_items length")

    if manifest.get("seed_tickers") != list(REQUIRED_SEED_TICKERS):
        errors.append("manifest seed_tickers must match required seed ticker order")

    status_policy = manifest.get("status_policy")
    if not isinstance(status_policy, Mapping):
        errors.append("manifest status_policy is required")
    else:
        if status_policy.get("candidate_card_exists") != ["MU"]:
            errors.append("manifest status_policy.candidate_card_exists must be ['MU']")
        if status_policy.get("intake_only") != ["DELL", "INTC", "AMD", "LRCX", "ALB"]:
            errors.append("manifest status_policy.intake_only must match intake-only seed tickers")

    source_policy = manifest.get("source_policy")
    if not isinstance(source_policy, Mapping):
        errors.append("manifest source_policy is required")
    else:
        canonical_sources = source_policy.get("canonical_sources")
        if canonical_sources not in ([], None):
            errors.append("manifest source_policy.canonical_sources must be empty for G8.1 intake")

    for list_field in ("allowed_use", "forbidden_use"):
        value = manifest.get(list_field)
        if not isinstance(value, list) or not value:
            errors.append(f"manifest {list_field} must be a non-empty list")


def _contains_forbidden_action_call(value: str) -> bool:
    normalized = _normalize_text(value)
    if normalized in {"buy", "sell", "hold", "buy/sell", "buy_sell", "buy sell"}:
        return True
    return any(
        token in normalized
        for token in (
            "buy signal",
            "sell signal",
            "hold signal",
            "buy rating",
            "sell rating",
            "hold rating",
            "buy call",
            "sell call",
            "hold call",
        )
    )


def _contains_forbidden_promotion_text(value: str) -> bool:
    normalized = _normalize_text(value)
    return any(pattern in normalized for pattern in FORBIDDEN_PROMOTION_TEXT)


def _is_forbidden_promotion_key(normalized_key: str) -> bool:
    if "candidate_card" not in normalized_key:
        return False
    return any(
        token in normalized_key
        for token in (
            "authority",
            "approved",
            "approval",
            "create",
            "created",
            "creation",
            "full",
            "new",
            "promote",
            "promotion",
            "second",
            "status",
        )
    )


def _validate_no_canonical_true_anywhere(obj: Any, errors: list[str]) -> None:
    for path, key, value in _walk_mapping_keys(obj):
        if _normalize_key(key) == "canonical" and value is True:
            errors.append(f"canonical=true is not allowed at {'.'.join((*path, key))}")


def _canonical_source_entries(obj: Any) -> list[Any]:
    entries: list[Any] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            normalized = _normalize_key(str(key))
            if normalized in {"canonical_source", "canonical_sources"}:
                if isinstance(value, list):
                    entries.extend(value)
                else:
                    entries.append(value)
            elif normalized in {"source_notes", "sources", "known_source_candidates"} and isinstance(value, list):
                entries.extend(
                    entry
                    for entry in value
                    if isinstance(entry, Mapping) and bool(entry.get("canonical"))
                )
            else:
                entries.extend(_canonical_source_entries(value))
    elif isinstance(obj, list):
        for item in obj:
            entries.extend(_canonical_source_entries(item))
    return entries


def _walk_mapping_keys(obj: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str, Any]]:
    entries: list[tuple[tuple[str, ...], str, Any]] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_text = str(key)
            entries.append((path, key_text, value))
            entries.extend(_walk_mapping_keys(value, (*path, key_text)))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, Mapping):
                entries.extend(_walk_mapping_keys(value, (*path, str(index))))
            elif isinstance(value, list):
                entries.extend(_walk_mapping_keys(value, (*path, str(index))))
            else:
                entries.append((path, str(index), value))
    return entries


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _origin_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return []


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _stringify(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_stringify(inner)}" for key, inner in value.items())
    if isinstance(value, list):
        return " ".join(_stringify(item) for item in value)
    return str(value)
