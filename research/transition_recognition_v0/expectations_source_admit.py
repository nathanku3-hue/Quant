"""TR-v0 bounded expectations source-admission gate.

This module is deliberately outcome-blind and provider-acquisition blind.  It
validates an already-bound source-semantic manifest plus already-landed local
bytes/receipt and returns either ``PASS_SOURCE_ADMITTED`` or ``HOLD_SOURCE``.

Raw provider bytes may be shared at custody level.  Family authority may not:
canonical rows emitted by this gate are bound to a TR-v0-specific receipt and
source id, and CRV1 expectation artifacts/receipts are rejected as authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.alpha_pit_v1.contracts import FamilyDataContract
from research.aov0.contracts import normalize_security_id
from research.transition_recognition_v0.l2_observation_contract import (
    PRIMARY_RECOGNITION_MEASURES,
    assert_l2_contract_invariants,
)

SLICE_ID = "TR-v0-L2B-EXPECTATIONS-SOURCE-ADMIT-1"
FAMILY_ID = "TRANSITION_RECOGNITION_v0"
PHASE = "L2B_SOURCE_ADMISSION"
PASS_TERMINAL = "PASS_SOURCE_ADMITTED"
HOLD_TERMINAL = "HOLD_SOURCE"
NEXT_ON_PASS = "TR-v0-L3-REPRESENTATION-SNR-1"
NEXT_ON_HOLD = "PARK_TR_v0"

CIQ_PROVIDER = "S&P Capital IQ Pro"
TR_EXPECTATIONS_SOURCE_ID = "SPCIQPRO:TR_V0_EXPECTATIONS"
CRV1_EXPECTATIONS_SOURCE_ID = "SPCIQPRO:CRV1_EXPECTATIONS"
SEMANTICS_SCHEMA = "tr_v0_expectations_source_semantics_v1"
RAW_CAPTURE_SCHEMA = "ciq_expectations_capture_v1"
SOURCE_RECEIPT_SCHEMA = "tr_v0_expectations_source_receipt_v1"
TR_FAMILY_AUTHORITY = "TRANSITION_RECOGNITION_v0_SOURCE_AUTHORITY"

REVISION_CONSTRUCTION_ID = "TR_V0_EPS_FY1_ABS_DELTA_SAME_FPE_LOOKBACK_V1"
REVISION_ORIGIN_DIRECT = "PROVIDER_OBSERVED"
REVISION_ORIGIN_DERIVED = "DETERMINISTIC_FROM_LAWFUL_EPS_FY1_HISTORY"

PRIMARY_MEASURES = tuple(PRIMARY_RECOGNITION_MEASURES)
PRIMARY_MEASURE_SET = frozenset(PRIMARY_MEASURES)
REVISION_LOOKBACK_DAYS = {
    "EPS_FY1_REVISION_30D": 30,
    "EPS_FY1_REVISION_90D": 90,
}

COVERAGE_STATUSES = frozenset(
    {
        "PRESENT",
        "MISSING_HISTORY",
        "MISSING_SOURCE",
        "NOT_ENTITLED",
        "NOT_APPLICABLE",
        "STALE",
    }
)
CANONICAL_ROW_KEYS = frozenset(
    {
        "security_id",
        "measure",
        "value",
        "forecast_period_end",
        "observed_at",
        "available_at",
        "source_id",
        "source_receipt_sha256",
        "epistemic_class",
        "coverage_status",
        "missingness_reason",
    }
)
RAW_ROW_KEYS = CANONICAL_ROW_KEYS - {"source_id", "source_receipt_sha256"}
FORBIDDEN_RAW_AUTHORITY_KEYS = frozenset(
    {"family_id", "source_id", "family_data_contract", "authority_class"}
)
PLACEHOLDER_TOKENS = ("UNBOUND", "UNKNOWN", "TBD", "TODO", "PLACEHOLDER", "BLOCKED_UNSET")

TR_V0_FAMILY_DATA_CONTRACT = FamilyDataContract(
    family_id=FAMILY_ID,
    risk_set_spec_id="TR_V0_USES_W3_DENOMINATOR_WHEN_EVALUATED_NOT_OWN_RISKSET_THIS_SLICE",
    primary_label_spec_id="UNSET_THIS_SLICE_NO_OUTCOMES",
    allowed_observation_surface=(),
    allowed_expectation_surface=PRIMARY_MEASURES,
    allowed_claim_surface=(),
)


@dataclass(frozen=True)
class SourceAdmissionDecision:
    terminal: str
    failed_gate: str | None
    reason: str | None
    semantics_sha256: str | None
    raw_sha256: str | None
    source_receipt_sha256: str | None
    admitted_rows: tuple[Mapping[str, Any], ...]

    @property
    def admitted(self) -> bool:
        return self.terminal == PASS_TERMINAL

    @property
    def next(self) -> str:
        return NEXT_ON_PASS if self.admitted else NEXT_ON_HOLD

    def as_dict(self) -> dict[str, Any]:
        return {
            "slice_id": SLICE_ID,
            "family_id": FAMILY_ID,
            "phase": PHASE,
            "terminal": self.terminal,
            "failed_gate": self.failed_gate,
            "reason": self.reason,
            "semantics_sha256": self.semantics_sha256,
            "raw_sha256": self.raw_sha256,
            "source_receipt_sha256": self.source_receipt_sha256,
            "admitted_row_count": len(self.admitted_rows),
            "next": self.next,
            "debit": 0,
            "evals": 0,
            "returns_join": False,
            "timing_research": False,
            "financial_alpha_evidence": 0,
        }


class SourceAdmissionError(ValueError):
    def __init__(self, gate: str, reason: str) -> None:
        super().__init__(reason)
        self.gate = gate
        self.reason = reason


def canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantics_sha256(semantics: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(semantics))


def evaluate_source_admission(
    *,
    decision_as_of: datetime,
    semantics: Mapping[str, Any] | None,
    raw_path: str | Path | None = None,
    source_receipt_path: str | Path | None = None,
) -> SourceAdmissionDecision:
    """Run G-S0 -> G-S1 -> G-S2 and return a terminal decision.

    The function does no provider/network work and never reads outcomes or
    returns.  Failure at any gate returns ``HOLD_SOURCE`` immediately.
    """

    # The already-frozen parent contract is a hard prerequisite and still owns
    # the no-trial/no-timing/no-returns law.
    try:
        assert_l2_contract_invariants()
    except (AssertionError, OSError, json.JSONDecodeError) as exc:
        return _hold("G-S0", f"PARENT_L2_CONTRACT_INVALID:{exc}")

    try:
        cutoff = _aware(decision_as_of, field="decision_as_of")
        if semantics is None:
            raise SourceAdmissionError("G-S0", "EXACT_CIQ_SOURCE_SEMANTICS_UNBOUND")
        _validate_source_semantics(semantics)
        sem_sha = semantics_sha256(semantics)
    except SourceAdmissionError as exc:
        return _hold(exc.gate, exc.reason)

    try:
        if raw_path is None or source_receipt_path is None:
            raise SourceAdmissionError("G-S1", "SOURCE_BYTES_AND_TR_RECEIPT_REQUIRED")
        raw_file = Path(raw_path)
        receipt_file = Path(source_receipt_path)
        if not raw_file.is_file() or not receipt_file.is_file():
            raise SourceAdmissionError("G-S1", "SOURCE_BYTES_OR_TR_RECEIPT_NOT_LANDED")
        raw_sha = sha256_file(raw_file)
        receipt_sha = sha256_file(receipt_file)
        receipt = _load_json(receipt_file, gate="G-S1", reason="TR_SOURCE_RECEIPT_INVALID_JSON")
        _validate_source_receipt(
            receipt,
            raw_path=raw_file,
            raw_sha256=raw_sha,
            semantics=semantics,
            semantics_sha256_value=sem_sha,
        )
    except (OSError, SourceAdmissionError) as exc:
        if isinstance(exc, SourceAdmissionError):
            return _hold(exc.gate, exc.reason, semantics_sha256_value=sem_sha)
        return _hold("G-S1", f"SOURCE_CUSTODY_READ_ERROR:{exc}", semantics_sha256_value=sem_sha)

    try:
        raw = _load_json(raw_file, gate="G-S2", reason="RAW_EXPECTATIONS_INVALID_JSON")
        admitted_rows = _validate_and_canonicalize_raw(
            raw,
            semantics=semantics,
            decision_as_of=cutoff,
            receipt_sha256=receipt_sha,
        )
    except (OSError, SourceAdmissionError) as exc:
        if isinstance(exc, SourceAdmissionError):
            return _hold(
                exc.gate,
                exc.reason,
                semantics_sha256_value=sem_sha,
                raw_sha256=raw_sha,
                source_receipt_sha256=receipt_sha,
            )
        return _hold(
            "G-S2",
            f"RAW_EXPECTATIONS_READ_ERROR:{exc}",
            semantics_sha256_value=sem_sha,
            raw_sha256=raw_sha,
            source_receipt_sha256=receipt_sha,
        )

    return SourceAdmissionDecision(
        terminal=PASS_TERMINAL,
        failed_gate=None,
        reason=None,
        semantics_sha256=sem_sha,
        raw_sha256=raw_sha,
        source_receipt_sha256=receipt_sha,
        admitted_rows=tuple(admitted_rows),
    )


def _hold(
    gate: str,
    reason: str,
    *,
    semantics_sha256_value: str | None = None,
    raw_sha256: str | None = None,
    source_receipt_sha256: str | None = None,
) -> SourceAdmissionDecision:
    return SourceAdmissionDecision(
        terminal=HOLD_TERMINAL,
        failed_gate=gate,
        reason=reason,
        semantics_sha256=semantics_sha256_value,
        raw_sha256=raw_sha256,
        source_receipt_sha256=source_receipt_sha256,
        admitted_rows=(),
    )


def _validate_source_semantics(semantics: Mapping[str, Any]) -> None:
    if not isinstance(semantics, Mapping):
        raise SourceAdmissionError("G-S0", "SOURCE_SEMANTICS_MAPPING_REQUIRED")
    if semantics.get("schema_version") != SEMANTICS_SCHEMA:
        raise SourceAdmissionError("G-S0", "SOURCE_SEMANTICS_SCHEMA_INVALID")
    if semantics.get("status") != "EXACT_BOUND":
        raise SourceAdmissionError("G-S0", "EXACT_CIQ_SOURCE_SEMANTICS_UNBOUND")
    if semantics.get("provider") != CIQ_PROVIDER:
        raise SourceAdmissionError("G-S0", "CIQ_PROVIDER_SEMANTICS_INVALID")

    _bound_text(semantics.get("provider_transport"), "PROVIDER_TRANSPORT_UNBOUND")

    identity = semantics.get("identity")
    if not isinstance(identity, Mapping):
        raise SourceAdmissionError("G-S0", "CIQSEC_IDENTITY_SEMANTICS_UNBOUND")
    if identity.get("namespace") != "CIQSEC":
        raise SourceAdmissionError("G-S0", "CIQSEC_IDENTITY_NAMESPACE_REQUIRED")
    _bound_text(identity.get("provider_identity_field"), "CIQSEC_PROVIDER_IDENTITY_FIELD_UNBOUND")
    _bound_text(identity.get("law"), "CIQSEC_IDENTITY_LAW_UNBOUND")

    historical = semantics.get("historical_as_of")
    if not isinstance(historical, Mapping):
        raise SourceAdmissionError("G-S0", "HISTORICAL_ASOF_SEMANTICS_UNBOUND")
    _bound_text(historical.get("provider_function_or_endpoint"), "HISTORICAL_ASOF_FUNCTION_UNBOUND")
    _bound_text(historical.get("law"), "HISTORICAL_ASOF_LAW_UNBOUND")

    availability = semantics.get("publication_availability")
    if not isinstance(availability, Mapping):
        raise SourceAdmissionError("G-S0", "PUBLICATION_AVAILABLE_AT_SEMANTICS_UNBOUND")
    _bound_text(availability.get("law"), "PUBLICATION_AVAILABLE_AT_LAW_UNBOUND")

    forecast = semantics.get("forecast_period")
    if not isinstance(forecast, Mapping):
        raise SourceAdmissionError("G-S0", "FORECAST_PERIOD_SEMANTICS_UNBOUND")
    _bound_text(forecast.get("eps_fy1_law"), "EPS_FY1_FORECAST_PERIOD_LAW_UNBOUND")
    _bound_text(forecast.get("forecast_period_end_field"), "FORECAST_PERIOD_END_FIELD_UNBOUND")

    independence = semantics.get("source_independence")
    if not isinstance(independence, Mapping):
        raise SourceAdmissionError("G-S0", "SOURCE_INDEPENDENCE_LAW_UNBOUND")
    if independence.get("recognition_source_is_not_reality_artifact") is not True:
        raise SourceAdmissionError("G-S0", "RECOGNITION_SOURCE_INDEPENDENCE_REQUIRED")
    if independence.get("family_authority_is_tr_specific") is not True:
        raise SourceAdmissionError("G-S0", "TR_SPECIFIC_FAMILY_AUTHORITY_REQUIRED")

    measures = semantics.get("measures")
    if not isinstance(measures, Mapping) or set(measures) != PRIMARY_MEASURE_SET:
        raise SourceAdmissionError("G-S0", "PRIMARY_MEASURE_SEMANTICS_EXACT_SET_REQUIRED")
    level = measures["EPS_FY1"]
    if not isinstance(level, Mapping) or level.get("origin") != REVISION_ORIGIN_DIRECT:
        raise SourceAdmissionError("G-S0", "EPS_FY1_PROVIDER_OBSERVED_SEMANTICS_REQUIRED")
    _bound_text(level.get("provider_field_or_function"), "EPS_FY1_PROVIDER_FIELD_UNBOUND")
    _bound_text(level.get("provider_period_argument"), "EPS_FY1_PROVIDER_PERIOD_UNBOUND")

    for measure, lookback in REVISION_LOOKBACK_DAYS.items():
        spec = measures[measure]
        if not isinstance(spec, Mapping):
            raise SourceAdmissionError("G-S0", f"{measure}_SEMANTICS_UNBOUND")
        origin = spec.get("origin")
        if origin == REVISION_ORIGIN_DIRECT:
            _bound_text(spec.get("provider_field_or_function"), f"{measure}_PROVIDER_FIELD_UNBOUND")
            _bound_text(spec.get("provider_period_argument"), f"{measure}_PROVIDER_PERIOD_UNBOUND")
        elif origin == REVISION_ORIGIN_DERIVED:
            if spec.get("construction_id") != REVISION_CONSTRUCTION_ID:
                raise SourceAdmissionError("G-S0", f"{measure}_CONSTRUCTION_ID_INVALID")
            if spec.get("lookback_calendar_days") != lookback:
                raise SourceAdmissionError("G-S0", f"{measure}_LOOKBACK_INVALID")
            if spec.get("base_measure") != "EPS_FY1":
                raise SourceAdmissionError("G-S0", f"{measure}_BASE_MEASURE_INVALID")
            if spec.get("forecast_period_alignment") != "SAME_FORECAST_PERIOD_END":
                raise SourceAdmissionError("G-S0", f"{measure}_FORECAST_ALIGNMENT_INVALID")
            if spec.get("vintage_selection_law") != "LATEST_PRESENT_AVAILABLE_AT_OR_BEFORE_LOOKBACK_CUTOFF":
                raise SourceAdmissionError("G-S0", f"{measure}_VINTAGE_SELECTION_LAW_INVALID")
            if spec.get("formula") != "CURRENT_EPS_FY1_MINUS_LOOKBACK_EPS_FY1":
                raise SourceAdmissionError("G-S0", f"{measure}_FORMULA_INVALID")
        else:
            raise SourceAdmissionError("G-S0", f"{measure}_ORIGIN_INVALID")


def _validate_source_receipt(
    receipt: Mapping[str, Any],
    *,
    raw_path: Path,
    raw_sha256: str,
    semantics: Mapping[str, Any],
    semantics_sha256_value: str,
) -> None:
    required = {
        "schema_version",
        "slice_id",
        "family_id",
        "source_id",
        "provider",
        "retrieved_at",
        "raw_object_path",
        "raw_object_sha256",
        "semantics_sha256",
        "license_scope",
        "retention_class",
        "family_authority",
        "crv1_artifact_authority_reused",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != required:
        raise SourceAdmissionError("G-S1", "TR_SOURCE_RECEIPT_FIELDS_INVALID")
    if receipt.get("schema_version") != SOURCE_RECEIPT_SCHEMA:
        raise SourceAdmissionError("G-S1", "TR_SOURCE_RECEIPT_SCHEMA_INVALID")
    if receipt.get("slice_id") != SLICE_ID or receipt.get("family_id") != FAMILY_ID:
        raise SourceAdmissionError("G-S1", "TR_SOURCE_RECEIPT_FAMILY_AUTHORITY_INVALID")
    if receipt.get("source_id") == CRV1_EXPECTATIONS_SOURCE_ID:
        raise SourceAdmissionError("G-S1", "CRV1_ARTIFACT_AS_TR_AUTHORITY_FORBIDDEN")
    if receipt.get("source_id") != TR_EXPECTATIONS_SOURCE_ID:
        raise SourceAdmissionError("G-S1", "TR_EXPECTATIONS_SOURCE_ID_REQUIRED")
    if receipt.get("provider") != semantics.get("provider"):
        raise SourceAdmissionError("G-S1", "TR_SOURCE_RECEIPT_PROVIDER_MISMATCH")
    if receipt.get("family_authority") != TR_FAMILY_AUTHORITY:
        raise SourceAdmissionError("G-S1", "TR_FAMILY_AUTHORITY_EXPLICIT_BIND_REQUIRED")
    if receipt.get("crv1_artifact_authority_reused") is not False:
        raise SourceAdmissionError("G-S1", "CRV1_ARTIFACT_AS_TR_AUTHORITY_FORBIDDEN")
    if receipt.get("raw_object_sha256") != raw_sha256:
        raise SourceAdmissionError("G-S1", "RAW_OBJECT_SHA256_MISMATCH")
    if receipt.get("semantics_sha256") != semantics_sha256_value:
        raise SourceAdmissionError("G-S1", "SOURCE_SEMANTICS_SHA256_MISMATCH")
    if Path(str(receipt.get("raw_object_path"))).name != raw_path.name:
        raise SourceAdmissionError("G-S1", "RAW_OBJECT_PATH_BINDING_MISMATCH")
    _aware_text(receipt.get("retrieved_at"), field="receipt_retrieved_at", gate="G-S1")
    _bound_text(receipt.get("license_scope"), "LICENSE_SCOPE_REQUIRED", gate="G-S1")
    _bound_text(receipt.get("retention_class"), "RETENTION_CLASS_REQUIRED", gate="G-S1")


def _validate_and_canonicalize_raw(
    raw: Mapping[str, Any],
    *,
    semantics: Mapping[str, Any],
    decision_as_of: datetime,
    receipt_sha256: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, Mapping):
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATIONS_MAPPING_REQUIRED")
    if FORBIDDEN_RAW_AUTHORITY_KEYS.intersection(raw):
        raise SourceAdmissionError("G-S2", "RAW_BYTES_MUST_NOT_CARRY_FAMILY_AUTHORITY")
    if set(raw) != {"schema_version", "provider", "rows"}:
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATIONS_TOP_LEVEL_FIELDS_INVALID")
    if raw.get("schema_version") != RAW_CAPTURE_SCHEMA:
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATIONS_SCHEMA_INVALID")
    if raw.get("provider") != semantics.get("provider"):
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATIONS_PROVIDER_MISMATCH")
    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATIONS_ROWS_REQUIRED")

    canonical_raw: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    direct_measures = {
        measure
        for measure, spec in semantics["measures"].items()
        if spec.get("origin") == REVISION_ORIGIN_DIRECT
    }
    allowed_raw_measures = {"EPS_FY1", *direct_measures}

    for raw_row in rows:
        row = _validate_raw_row(raw_row, decision_as_of=decision_as_of)
        measure = row["measure"]
        if measure not in allowed_raw_measures:
            raise SourceAdmissionError("G-S2", f"RAW_MEASURE_NOT_AUTHORIZED_BY_SEMANTICS:{measure}")
        key = (row["security_id"], measure, row["available_at"])
        if key in seen:
            raise SourceAdmissionError("G-S2", "DUPLICATE_SECURITY_MEASURE_AVAILABLE_AT_KEY")
        seen.add(key)
        canonical_raw.append(row)

    _require_level_history_for_all_securities(canonical_raw)
    output_rows = [
        _bind_tr_authority(row, receipt_sha256=receipt_sha256)
        for row in canonical_raw
        if row["measure"] in direct_measures
    ]

    for measure, lookback in REVISION_LOOKBACK_DAYS.items():
        spec = semantics["measures"][measure]
        if spec.get("origin") == REVISION_ORIGIN_DERIVED:
            output_rows.extend(
                _derive_revision_rows(
                    canonical_raw,
                    measure=measure,
                    lookback_days=lookback,
                    receipt_sha256=receipt_sha256,
                )
            )

    output_rows.sort(key=lambda row: (row["security_id"], row["measure"], row["available_at"]))
    output_seen: set[tuple[str, str, str]] = set()
    for row in output_rows:
        if set(row) != CANONICAL_ROW_KEYS:
            raise SourceAdmissionError("G-S2", "CANONICAL_EXPECTATION_ROW_FIELDS_INVALID")
        key = (row["security_id"], row["measure"], row["available_at"])
        if key in output_seen:
            raise SourceAdmissionError("G-S2", "CANONICAL_DUPLICATE_KEY")
        output_seen.add(key)
    return output_rows


def _validate_raw_row(raw_row: Any, *, decision_as_of: datetime) -> dict[str, Any]:
    if not isinstance(raw_row, Mapping) or set(raw_row) != RAW_ROW_KEYS:
        raise SourceAdmissionError("G-S2", "RAW_EXPECTATION_ROW_FIELDS_INVALID_NO_TICKER_FALLBACK")
    try:
        security_id = normalize_security_id(raw_row.get("security_id"))
    except ValueError as exc:
        raise SourceAdmissionError("G-S2", f"CIQSEC_IDENTITY_REQUIRED:{exc}") from exc
    measure = str(raw_row.get("measure") or "")
    if measure not in PRIMARY_MEASURE_SET:
        raise SourceAdmissionError("G-S2", f"UNKNOWN_OR_PARKED_EXPECTATION_MEASURE:{measure}")
    observed = _aware_text(raw_row.get("observed_at"), field="observed_at", gate="G-S2")
    available = _aware_text(raw_row.get("available_at"), field="available_at", gate="G-S2")
    if observed > available:
        raise SourceAdmissionError("G-S2", "OBSERVED_AT_AFTER_AVAILABLE_AT")
    if available > decision_as_of:
        raise SourceAdmissionError("G-S2", "AVAILABLE_AT_AFTER_DECISION_AS_OF")

    coverage = str(raw_row.get("coverage_status") or "")
    if coverage not in COVERAGE_STATUSES:
        raise SourceAdmissionError("G-S2", f"COVERAGE_STATUS_INVALID:{coverage}")
    if raw_row.get("epistemic_class") != "OBSERVED_CONSENSUS":
        raise SourceAdmissionError("G-S2", "OBSERVED_CONSENSUS_EPISTEMIC_CLASS_REQUIRED")

    value = raw_row.get("value")
    missingness = raw_row.get("missingness_reason")
    if coverage == "PRESENT":
        if not _finite_number(value):
            raise SourceAdmissionError("G-S2", "PRESENT_EXPECTATION_VALUE_FINITE_REQUIRED")
        if missingness not in (None, ""):
            raise SourceAdmissionError("G-S2", "PRESENT_EXPECTATION_MISSINGNESS_MUST_BE_NULL")
    else:
        if value is not None:
            raise SourceAdmissionError("G-S2", "MISSING_EXPECTATION_VALUE_MUST_BE_NULL")
        if not str(missingness or "").strip():
            raise SourceAdmissionError("G-S2", "MISSINGNESS_REASON_REQUIRED")

    fpe = raw_row.get("forecast_period_end")
    if coverage == "PRESENT":
        _date_text(fpe, field="forecast_period_end")
    elif fpe not in (None, ""):
        _date_text(fpe, field="forecast_period_end")

    return {
        "security_id": security_id,
        "measure": measure,
        "value": float(value) if coverage == "PRESENT" else None,
        "forecast_period_end": None if fpe in (None, "") else str(fpe),
        "observed_at": _utc_text(observed),
        "available_at": _utc_text(available),
        "epistemic_class": "OBSERVED_CONSENSUS",
        "coverage_status": coverage,
        "missingness_reason": None if coverage == "PRESENT" else str(missingness),
    }


def _require_level_history_for_all_securities(rows: Sequence[Mapping[str, Any]]) -> None:
    securities = {str(row["security_id"]) for row in rows}
    level_securities = {
        str(row["security_id"])
        for row in rows
        if row["measure"] == "EPS_FY1"
    }
    missing = sorted(securities - level_securities)
    if missing:
        raise SourceAdmissionError("G-S2", "EPS_FY1_LEVEL_HISTORY_REQUIRED_FOR_EVERY_SECURITY")


def _derive_revision_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    measure: str,
    lookback_days: int,
    receipt_sha256: str,
) -> list[dict[str, Any]]:
    levels = [row for row in rows if row["measure"] == "EPS_FY1"]
    by_security: dict[str, list[Mapping[str, Any]]] = {}
    for row in levels:
        by_security.setdefault(str(row["security_id"]), []).append(row)
    for security_rows in by_security.values():
        security_rows.sort(key=lambda row: str(row["available_at"]))

    derived: list[dict[str, Any]] = []
    for current in levels:
        current_available = _parse_utc(str(current["available_at"]), field="available_at", gate="G-S2")
        fpe = current.get("forecast_period_end")
        base_candidates = [
            prior
            for prior in by_security[str(current["security_id"])]
            if prior["coverage_status"] == "PRESENT"
            and prior.get("forecast_period_end") == fpe
            and _parse_utc(str(prior["available_at"]), field="available_at", gate="G-S2")
            <= current_available - timedelta(days=lookback_days)
        ]
        if current["coverage_status"] != "PRESENT":
            value = None
            coverage = str(current["coverage_status"])
            reason = f"CURRENT_EPS_FY1_UNAVAILABLE:{current['missingness_reason']}"
        elif not base_candidates:
            value = None
            coverage = "MISSING_HISTORY"
            reason = f"NO_SAME_FPE_PRESENT_EPS_FY1_AT_OR_BEFORE_{lookback_days}D_LOOKBACK"
        else:
            prior = max(base_candidates, key=lambda row: str(row["available_at"]))
            value = float(current["value"]) - float(prior["value"])
            coverage = "PRESENT"
            reason = None
        derived.append(
            {
                "security_id": current["security_id"],
                "measure": measure,
                "value": value,
                "forecast_period_end": fpe,
                "observed_at": current["observed_at"],
                "available_at": current["available_at"],
                "source_id": TR_EXPECTATIONS_SOURCE_ID,
                "source_receipt_sha256": receipt_sha256,
                "epistemic_class": "OBSERVED_CONSENSUS",
                "coverage_status": coverage,
                "missingness_reason": reason,
            }
        )
    return derived


def _bind_tr_authority(row: Mapping[str, Any], *, receipt_sha256: str) -> dict[str, Any]:
    return {
        **dict(row),
        "source_id": TR_EXPECTATIONS_SOURCE_ID,
        "source_receipt_sha256": receipt_sha256,
    }


def _load_json(path: Path, *, gate: str, reason: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceAdmissionError(gate, reason) from exc
    if not isinstance(payload, Mapping):
        raise SourceAdmissionError(gate, reason)
    return payload


def _bound_text(value: Any, reason: str, *, gate: str = "G-S0") -> str:
    text = str(value or "").strip()
    if not text or any(token in text.upper() for token in PLACEHOLDER_TOKENS):
        raise SourceAdmissionError(gate, reason)
    return text


def _aware(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SourceAdmissionError("G-S2", f"{field.upper()}_TIMEZONE_AWARE_REQUIRED")
    return value.astimezone(UTC)


def _aware_text(value: Any, *, field: str, gate: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SourceAdmissionError(gate, f"{field.upper()}_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceAdmissionError(gate, f"{field.upper()}_TIMEZONE_AWARE_REQUIRED")
    return parsed.astimezone(UTC)


def _parse_utc(value: str, *, field: str, gate: str) -> datetime:
    return _aware_text(value, field=field, gate=gate)


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _date_text(value: Any, *, field: str) -> str:
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise SourceAdmissionError("G-S2", f"{field.upper()}_DATE_REQUIRED") from exc
    return parsed.isoformat()


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and number not in (float("inf"), float("-inf"))
