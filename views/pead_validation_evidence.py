"""Read-only PEAD evidence readiness board."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st


DEFAULT_VALIDATION_EVIDENCE_PATH = Path(
    "docs/context/e2e_evidence/pead_real_data_validation_full_universe_v2.json"
)
DEFAULT_M1B_EVIDENCE_PATH = Path(
    "docs/context/e2e_evidence/pead_calendar_time_inference_m1b_full_universe_v2.json"
)
LEGACY_VALIDATION_EVIDENCE_PATH = Path(
    "docs/context/e2e_evidence/pead_real_data_validation_20260620.json"
)
LEGACY_M1B_EVIDENCE_PATH = Path(
    "docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json"
)
EXPECTED_VALIDATION_EVIDENCE_SHA256 = (
    "eaba0342f8a73e13baebf98f282eea29222fb815c9793072698a3f47ded1a021"
)
EXPECTED_M1B_EVIDENCE_SHA256 = (
    "07c20f22b4d10f6e11775aba15e76433665a7eaeebb866e64306ec33da61410d"
)
EXPECTED_LEGACY_VALIDATION_EVIDENCE_SHA256 = (
    "96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e"
)
EXPECTED_LEGACY_M1B_EVIDENCE_SHA256 = (
    "c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76"
)
EXPECTED_EVIDENCE_SHA256 = EXPECTED_VALIDATION_EVIDENCE_SHA256
REVIEW_ONLY_TITLE = "PEAD Evidence Readiness - Read Only"
REVIEW_ONLY_WARNING = (
    "Evidence readiness only. Alpha interpretation, strategy promotion, ranking, "
    "recommendations, alerts, and broker/order paths remain blocked."
)
EXPECTED_FULL_UNIVERSE_LIMITATIONS = (
    "full universe (9,969 issuers)",
    "current-vintage EPS",
    "Compustat return proxy",
    "no delisting adjustment",
)
EXPECTED_LEGACY_LIMITATIONS = (
    "500-GVKEY sample",
    "current-vintage EPS",
    "Compustat return proxy",
    "no delisting adjustment",
)
EXPECTED_LIMITATIONS = EXPECTED_LEGACY_LIMITATIONS
EXPECTED_M1B_FORBIDDEN_USE = (
    "alerts",
    "alpha_claims",
    "broker_or_order_paths",
    "causal_claims",
    "full_factor_alpha_claims",
    "net_performance_claims",
    "population_validity_claims",
    "ranking_or_scoring",
    "recommendations",
    "strategy_promotion",
    "strict_point_in_time_claims",
    "tradability_claims",
)
_COUNT_KEYS = ("rows", "events", "issuers", "eligible_events", "ineligible_events")
_LINEAGE_KEYS = ("d1", "d2b", "d3")


class PeadValidationEvidenceError(RuntimeError):
    """Raised when PEAD evidence cannot be safely rendered."""


@dataclass(frozen=True)
class PeadLineageSummary:
    label: str
    manifest_path: str
    manifest_sha256: str
    parquet_path: str
    parquet_sha256: str
    row_count: int


@dataclass(frozen=True)
class PeadValidationEvidence:
    path: Path
    sha256: str
    round_id: str
    mode: str
    counts: dict[str, int]
    lineage: tuple[PeadLineageSummary, ...]
    daily_hac_gap_count: int
    quarterly_descriptive_only: bool
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PeadM1BEvidence:
    path: Path
    sha256: str
    schema_version: str
    publishable: bool
    parent_sha256: str | None
    round_id: str
    scope_id: str
    method_id: str
    retained_sessions: int
    authoritative_sessions: int
    retained_date_min: str
    retained_date_max: str
    extreme_expected_rows: int
    extreme_missing_rows: int
    null_return_date_rows_excluded: int
    internal_gap_count: int
    primary_status: str
    primary_observations: int
    hac_maxlags_used: int
    minimum_finite_per_leg: int
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PeadEvidenceStatus:
    validation: PeadValidationEvidence
    m1b: PeadM1BEvidence
    legacy_validation: PeadValidationEvidence | None = None
    legacy_m1b: PeadM1BEvidence | None = None


def compute_file_sha256(path: Path) -> str:
    return hashlib.sha256(_read_evidence_bytes(path)).hexdigest()


def _read_evidence_bytes(path: Path) -> bytes:
    if not path.exists():
        raise PeadValidationEvidenceError(f"evidence JSON missing: {path}")
    if not path.is_file():
        raise PeadValidationEvidenceError(f"evidence path is not a file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PeadValidationEvidenceError(
            f"evidence JSON could not be read: {path}: {exc}"
        ) from exc


def _load_json_payload(
    path: Path | str,
    *,
    expected_sha256: str,
) -> tuple[Path, str, dict[str, Any]]:
    evidence_path = Path(path)
    evidence_bytes = _read_evidence_bytes(evidence_path)
    actual_sha256 = hashlib.sha256(evidence_bytes).hexdigest()
    if actual_sha256.lower() != expected_sha256.lower():
        raise PeadValidationEvidenceError(
            "evidence JSON SHA256 mismatch: "
            f"expected {expected_sha256.lower()}, got {actual_sha256.lower()}"
        )

    try:
        payload = json.loads(evidence_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PeadValidationEvidenceError(f"evidence JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise PeadValidationEvidenceError("evidence JSON root must be an object")
    return evidence_path, actual_sha256.lower(), payload


def load_pead_validation_evidence(
    path: Path | str = DEFAULT_VALIDATION_EVIDENCE_PATH,
    *,
    expected_sha256: str = EXPECTED_VALIDATION_EVIDENCE_SHA256,
    expected_limitations: tuple[str, ...] = EXPECTED_FULL_UNIVERSE_LIMITATIONS,
) -> PeadValidationEvidence:
    evidence_path, actual_sha256, payload = _load_json_payload(
        path,
        expected_sha256=expected_sha256,
    )

    if _require_str(payload, "artifact_name") != "pead_real_data_validation":
        raise PeadValidationEvidenceError("unexpected PEAD evidence artifact_name")
    _validate_validation_policy(_require_mapping(payload, "evidence_policy"))

    counts = _load_counts(payload)
    lineage = _load_lineage(payload)
    outputs = _require_mapping(payload, "outputs")
    event_date = _require_mapping(outputs, "event_date")
    quarterly = _require_mapping(outputs, "quarterly")
    daily_gap_count = _load_daily_hac_warning(event_date)
    quarterly_descriptive_only = _require_bool(quarterly, "ex_post_descriptive_only")
    if not quarterly_descriptive_only:
        raise PeadValidationEvidenceError(
            "quarterly output is not marked ex_post_descriptive_only = true"
        )

    limitations = _load_limitations(payload, expected_limitations=expected_limitations)
    return PeadValidationEvidence(
        path=evidence_path,
        sha256=actual_sha256,
        round_id=_require_str(payload, "round_id"),
        mode=_require_str(payload, "mode"),
        counts=counts,
        lineage=lineage,
        daily_hac_gap_count=daily_gap_count,
        quarterly_descriptive_only=quarterly_descriptive_only,
        limitations=limitations,
    )


def load_pead_m1b_evidence(
    path: Path | str = DEFAULT_M1B_EVIDENCE_PATH,
    *,
    expected_sha256: str = EXPECTED_M1B_EVIDENCE_SHA256,
    expected_schema_version: str = "2.0",
    expected_sample_universe: str = "full_universe",
    require_publishable: bool = True,
) -> PeadM1BEvidence:
    evidence_path, actual_sha256, payload = _load_json_payload(
        path,
        expected_sha256=expected_sha256,
    )

    schema_version = _require_str(payload, "schema_version")
    if schema_version != expected_schema_version:
        raise PeadValidationEvidenceError("unexpected M1B schema_version")
    if schema_version == "2.0":
        if _require_str(payload, "artifact_name") != "pead_calendar_time_inference_m1b":
            raise PeadValidationEvidenceError("unexpected M1B artifact_name")
    publishable = bool(payload.get("publishable")) if schema_version == "2.0" else False
    if require_publishable and not publishable:
        raise PeadValidationEvidenceError("M1B publishable flag is not true")
    parent_sha256 = payload.get("parent_sha256")
    if schema_version == "2.0":
        if not isinstance(parent_sha256, str) or not _is_sha256(parent_sha256):
            raise PeadValidationEvidenceError("M1B parent_sha256 is invalid")
    else:
        parent_sha256 = None

    method_id = _require_str(payload, "method_id")
    if method_id != "calendar_time_q5_q1_single_factor_hac59_v1":
        raise PeadValidationEvidenceError("unexpected M1B method_id")

    _validate_m1b_policy(_require_mapping(payload, "evidence_policy"))

    formation = _require_mapping(payload, "formation")
    minimum_finite_per_leg = _require_positive_int(
        formation,
        "minimum_finite_per_leg",
    )
    if minimum_finite_per_leg != 10:
        raise PeadValidationEvidenceError(
            "M1B minimum_finite_per_leg must remain 10"
        )

    session_coverage = _require_mapping(payload, "session_coverage")
    internal_gap_count = _require_nonnegative_int(session_coverage, "internal_gap_count")
    if internal_gap_count != 0:
        raise PeadValidationEvidenceError("M1B internal_gap_count must remain 0")

    primary_inference = _require_mapping(payload, "primary_inference")
    primary_status = _require_str(primary_inference, "status")
    if primary_status != "valid":
        raise PeadValidationEvidenceError("M1B primary inference is not valid")
    hac_maxlags_used = _require_positive_int(primary_inference, "hac_maxlags_used")
    if hac_maxlags_used != 59:
        raise PeadValidationEvidenceError("M1B HAC maxlags must remain 59")
    if not _require_bool(primary_inference, "use_correction"):
        raise PeadValidationEvidenceError("M1B HAC correction flag must remain true")

    return PeadM1BEvidence(
        path=evidence_path,
        sha256=actual_sha256,
        schema_version=schema_version,
        publishable=publishable,
        parent_sha256=parent_sha256,
        round_id=_require_str(payload, "round_id"),
        scope_id=_require_str(payload, "scope_id"),
        method_id=method_id,
        retained_sessions=_require_positive_int(session_coverage, "retained_sessions"),
        authoritative_sessions=_require_positive_int(
            session_coverage,
            "authoritative_sessions",
        ),
        retained_date_min=_require_str(session_coverage, "retained_date_min"),
        retained_date_max=_require_str(session_coverage, "retained_date_max"),
        extreme_expected_rows=_require_positive_int(
            session_coverage,
            "extreme_expected_rows",
        ),
        extreme_missing_rows=_require_nonnegative_int(
            session_coverage,
            "extreme_missing_rows",
        ),
        null_return_date_rows_excluded=_require_nonnegative_int(
            session_coverage,
            "null_return_date_rows_excluded",
        ),
        internal_gap_count=internal_gap_count,
        primary_status=primary_status,
        primary_observations=_require_positive_int(primary_inference, "observations"),
        hac_maxlags_used=hac_maxlags_used,
        minimum_finite_per_leg=minimum_finite_per_leg,
        limitations=_load_m1b_limitations(payload, expected_sample_universe=expected_sample_universe),
    )


def load_pead_evidence_status(
    validation_path: Path | str = DEFAULT_VALIDATION_EVIDENCE_PATH,
    m1b_path: Path | str = DEFAULT_M1B_EVIDENCE_PATH,
    *,
    expected_validation_sha256: str = EXPECTED_VALIDATION_EVIDENCE_SHA256,
    expected_m1b_sha256: str = EXPECTED_M1B_EVIDENCE_SHA256,
    legacy_validation_path: Path | str = LEGACY_VALIDATION_EVIDENCE_PATH,
    legacy_m1b_path: Path | str = LEGACY_M1B_EVIDENCE_PATH,
    expected_legacy_validation_sha256: str = EXPECTED_LEGACY_VALIDATION_EVIDENCE_SHA256,
    expected_legacy_m1b_sha256: str = EXPECTED_LEGACY_M1B_EVIDENCE_SHA256,
) -> PeadEvidenceStatus:
    validation = load_pead_validation_evidence(
        validation_path,
        expected_sha256=expected_validation_sha256,
        expected_limitations=EXPECTED_FULL_UNIVERSE_LIMITATIONS,
    )
    m1b = load_pead_m1b_evidence(
        m1b_path,
        expected_sha256=expected_m1b_sha256,
        expected_schema_version="2.0",
        expected_sample_universe="full_universe",
        require_publishable=True,
    )
    if m1b.parent_sha256 != validation.sha256:
        raise PeadValidationEvidenceError("M1B parent hash linkage mismatch")

    legacy_validation = load_pead_validation_evidence(
        legacy_validation_path,
        expected_sha256=expected_legacy_validation_sha256,
        expected_limitations=EXPECTED_LEGACY_LIMITATIONS,
    )
    legacy_m1b = load_pead_m1b_evidence(
        legacy_m1b_path,
        expected_sha256=expected_legacy_m1b_sha256,
        expected_schema_version="1.0",
        expected_sample_universe="fixed_500_gvkey_current_vintage_sample",
        require_publishable=False,
    )
    return PeadEvidenceStatus(
        validation=validation,
        m1b=m1b,
        legacy_validation=legacy_validation,
        legacy_m1b=legacy_m1b,
    )


def render_pead_validation_evidence(
    path: Path | str = DEFAULT_VALIDATION_EVIDENCE_PATH,
    *,
    expected_sha256: str = EXPECTED_VALIDATION_EVIDENCE_SHA256,
    m1b_path: Path | str = DEFAULT_M1B_EVIDENCE_PATH,
    expected_m1b_sha256: str = EXPECTED_M1B_EVIDENCE_SHA256,
    legacy_validation_path: Path | str = LEGACY_VALIDATION_EVIDENCE_PATH,
    legacy_m1b_path: Path | str = LEGACY_M1B_EVIDENCE_PATH,
    expected_legacy_validation_sha256: str = EXPECTED_LEGACY_VALIDATION_EVIDENCE_SHA256,
    expected_legacy_m1b_sha256: str = EXPECTED_LEGACY_M1B_EVIDENCE_SHA256,
) -> PeadEvidenceStatus | None:
    st.subheader(REVIEW_ONLY_TITLE)

    try:
        status = load_pead_evidence_status(
            path,
            m1b_path,
            expected_validation_sha256=expected_sha256,
            expected_m1b_sha256=expected_m1b_sha256,
            legacy_validation_path=legacy_validation_path,
            legacy_m1b_path=legacy_m1b_path,
            expected_legacy_validation_sha256=expected_legacy_validation_sha256,
            expected_legacy_m1b_sha256=expected_legacy_m1b_sha256,
        )
    except PeadValidationEvidenceError:
        st.error(
            "PEAD evidence readiness failed closed. Locked evidence did not pass "
            "verification."
        )
        return None

    st.warning(REVIEW_ONLY_WARNING)
    st.caption("Primary v2 evidence pair")
    st.markdown("**Readiness**")
    st.table(_build_readiness_rows())

    cols = st.columns(5)
    metrics = (
        ("Events", status.validation.counts["events"]),
        ("Eligible", status.validation.counts["eligible_events"]),
        ("Issuers", status.validation.counts["issuers"]),
        ("Retained Sessions", status.m1b.retained_sessions),
        ("Internal Gaps", status.m1b.internal_gap_count),
    )
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, _format_int(value))

    st.markdown("**Status Notes**")
    st.markdown("- Primary full-universe evidence pair passes schema, publishable, and parent-link checks.")
    st.markdown("- M1B methodology evidence is read-only and is not an alpha verdict.")
    st.markdown("- Strategy promotion, ranking, recommendations, alerts, and broker/order paths remain blocked.")
    st.markdown(
        "- Calendar-time coverage uses "
        f"{_format_int(status.m1b.retained_sessions)} retained sessions from "
        f"{status.m1b.retained_date_min} through {status.m1b.retained_date_max}."
    )

    st.markdown("**Active Limits**")
    for limitation in _combined_limitations(status):
        st.markdown(f"- {limitation}")

    with st.expander("Legacy sample comparison", expanded=False):
        st.table(_build_legacy_rows(status))

    return status


def _build_readiness_rows() -> list[dict[str, str]]:
    return [
        {
            "Item": "Primary v2 evidence pair",
            "State": "Pass",
            "Meaning": "Full-universe validation and M1B child are hash-linked and read-only.",
        },
        {
            "Item": "Dashboard readiness",
            "State": "Ready",
            "Meaning": "Use as minimal evidence/readiness status only.",
        },
        {
            "Item": "Legacy sample comparison",
            "State": "Folded",
            "Meaning": "Available only as secondary context.",
        },
        {
            "Item": "Alpha / product actions",
            "State": "Blocked",
            "Meaning": "Separate Alpha Interpretation Gate required.",
        },
    ]


def _build_legacy_rows(status: PeadEvidenceStatus) -> list[dict[str, str]]:
    if status.legacy_validation is None or status.legacy_m1b is None:
        return []
    return [
        {
            "Item": "Legacy events",
            "Primary v2": _format_int(status.validation.counts["events"]),
            "Legacy sample": _format_int(status.legacy_validation.counts["events"]),
        },
        {
            "Item": "Legacy issuers",
            "Primary v2": _format_int(status.validation.counts["issuers"]),
            "Legacy sample": _format_int(status.legacy_validation.counts["issuers"]),
        },
        {
            "Item": "Legacy retained sessions",
            "Primary v2": _format_int(status.m1b.retained_sessions),
            "Legacy sample": _format_int(status.legacy_m1b.retained_sessions),
        },
    ]


def _combined_limitations(status: PeadEvidenceStatus) -> tuple[str, ...]:
    combined = list(status.validation.limitations)
    for item in status.m1b.limitations:
        if item not in combined:
            combined.append(item)
    return tuple(combined)


def _load_counts(payload: dict[str, Any]) -> dict[str, int]:
    counts_payload = _require_mapping(payload, "counts")
    return {key: _require_int(counts_payload, key) for key in _COUNT_KEYS}


def _load_lineage(payload: dict[str, Any]) -> tuple[PeadLineageSummary, ...]:
    lineage_payload = _require_mapping(payload, "lineage")
    labels = {
        "d1": "D1 SUE",
        "d2b": "D2B Event Windows",
        "d3": "D3 Benchmark",
    }
    lineage: list[PeadLineageSummary] = []
    for key in _LINEAGE_KEYS:
        item = _require_mapping(lineage_payload, key)
        lineage.append(
            PeadLineageSummary(
                label=labels[key],
                manifest_path=_require_str(item, "manifest_path"),
                manifest_sha256=_require_str(item, "manifest_sha256"),
                parquet_path=_require_str(item, "parquet_path"),
                parquet_sha256=_require_str(item, "parquet_sha256"),
                row_count=_require_int(item, "row_count"),
            )
        )
    return tuple(lineage)


def _load_daily_hac_warning(event_date: dict[str, Any]) -> int:
    metrics = _require_mapping(event_date, "metrics")
    gap_counts: set[int] = set()
    for metric_name in ("car", "bhar"):
        metric = _require_mapping(metrics, metric_name)
        hac = _require_mapping(metric, "hac")
        gap_count = _require_int(hac, "observed_cohort_gap_count")
        if gap_count <= 0:
            raise PeadValidationEvidenceError(
                f"{metric_name} daily HAC gap count must be positive"
            )
        if hac.get("standard_error") is not None or hac.get("t_stat") is not None:
            raise PeadValidationEvidenceError(
                f"{metric_name} daily HAC SE/t-stat must be null when gaps exist"
            )
        gap_counts.add(gap_count)
    if len(gap_counts) != 1:
        raise PeadValidationEvidenceError("daily CAR/BHAR HAC gap counts disagree")
    return gap_counts.pop()


def _load_limitations(
    payload: dict[str, Any],
    *,
    expected_limitations: tuple[str, ...],
) -> tuple[str, ...]:
    value = payload.get("limitations")
    if not isinstance(value, list) or not value:
        raise PeadValidationEvidenceError("limitations must be a non-empty list")
    limitations: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise PeadValidationEvidenceError("limitations contain an unreadable item")
        limitations.append(item.strip())
    missing = [item for item in expected_limitations if item not in limitations]
    if missing:
        raise PeadValidationEvidenceError(
            "limitations missing required field(s): " + ", ".join(missing)
        )
    return tuple(limitations)


def _load_m1b_limitations(
    payload: dict[str, Any],
    *,
    expected_sample_universe: str,
) -> tuple[str, ...]:
    limitations = _require_mapping(payload, "limitations")
    required = {
        "sample_universe": expected_sample_universe,
        "eps_vintage": "current_vintage_compustat_eps",
        "return_source": "compustat_total_return_proxy",
        "delisting_adjustment": "none",
        "factor_model": "single_factor_mktrf_gross_equal_weight_q5_minus_q1",
    }
    for key, expected in required.items():
        if _require_str(limitations, key) != expected:
            raise PeadValidationEvidenceError(f"M1B limitation drift: {key}")
    universe = "full universe" if expected_sample_universe == "full_universe" else "fixed 500-GVKEY sample"
    return (
        universe,
        "current-vintage EPS",
        "Compustat total return proxy",
        "no delisting adjustment",
        "single-factor gross equal-weight Q5-minus-Q1 only",
    )


def _validate_validation_policy(policy: dict[str, Any]) -> None:
    if _require_bool(policy, "interpretation_performed"):
        raise PeadValidationEvidenceError(
            "evidence policy reports interpretation_performed = true"
        )
    forbidden = policy.get("forbidden_use")
    if isinstance(forbidden, list):
        required = ("alpha claims", "strategy promotion", "ranking/scoring", "alerts", "broker/order paths")
        missing = [item for item in required if item not in forbidden]
        if missing:
            raise PeadValidationEvidenceError(
                "validation forbidden_use missing required field(s): " + ", ".join(missing)
            )


def _validate_m1b_policy(policy: dict[str, Any]) -> None:
    if _require_str(policy, "allowed_use") != "bounded_methodology_review_only":
        raise PeadValidationEvidenceError("M1B allowed_use drift")
    if _require_bool(policy, "interpretation_performed"):
        raise PeadValidationEvidenceError(
            "M1B policy reports interpretation_performed = true"
        )
    for key in (
        "strategy_promotion_authorized",
        "ranking_or_scoring_authorized",
        "alerts_or_recommendations_authorized",
        "broker_or_order_path_authorized",
    ):
        if _require_bool(policy, key):
            raise PeadValidationEvidenceError(f"M1B policy reports {key} = true")

    forbidden_use = policy.get("forbidden_use")
    if not isinstance(forbidden_use, list):
        raise PeadValidationEvidenceError("M1B forbidden_use must be a list")
    missing = [item for item in EXPECTED_M1B_FORBIDDEN_USE if item not in forbidden_use]
    if missing:
        raise PeadValidationEvidenceError(
            "M1B forbidden_use missing required field(s): " + ", ".join(missing)
        )


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PeadValidationEvidenceError(f"required schema field missing: {key}")
    return value


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PeadValidationEvidenceError(f"required schema field missing: {key}")
    return value


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise PeadValidationEvidenceError(f"required integer field missing: {key}")
    return value


def _require_nonnegative_int(payload: dict[str, Any], key: str) -> int:
    value = _require_int(payload, key)
    if value < 0:
        raise PeadValidationEvidenceError(f"required nonnegative integer: {key}")
    return value


def _require_positive_int(payload: dict[str, Any], key: str) -> int:
    value = _require_int(payload, key)
    if value <= 0:
        raise PeadValidationEvidenceError(f"required positive integer: {key}")
    return value


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise PeadValidationEvidenceError(f"required boolean field missing: {key}")
    return value


def _is_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _format_int(value: int) -> str:
    return f"{value:,}"
