"""Shadow-only adapter for Leningrad financial-clearing evidence.

This module consumes an externally verified four-file Leningrad finance bundle.
It does not import or copy the clearing solver, interpret intervention targets as
securities, rank names, generate entries/exits, or authorize capital. Its only
research action is a point-in-time gross-exposure cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


CHOICE_SCENARIO_SCHEMA = "finance-intervention-choice-scenario-v2"
CHOICE_COMPARISON_SCHEMA = "finance-intervention-choice-comparison-v2"
CHOICE_BUNDLE_SCHEMA = "finance-intervention-choice-bundle-v2"
CLEARING_RESULT_SCHEMA = "finance-clearing-result-v1"
_REQUIRED_BUNDLE_FILES = frozenset(
    {"scenario.json", "comparison.json", "report.md", "bundle_index.json"}
)
CLAIM_BOUNDARY = (
    "Counterparty-payment cascade shadow evidence only; not an alpha generator, "
    "security selector, entry/exit signal, bailout trade, hedge instruction, or "
    "capital authority."
)


class FinancialCascadeError(ValueError):
    """Fail-closed financial-cascade adapter error."""


class CascadeRiskState(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    CLEAR = "CLEAR"
    WATCH = "WATCH"
    SEVERE = "SEVERE"


@dataclass(frozen=True, slots=True)
class FinancialCascadePolicy:
    """Explicit challenger policy; no continuous pseudo-precision score."""

    severe_default_fraction: Fraction = Fraction(1, 3)
    severe_unpaid_fraction: Fraction = Fraction(1, 10)
    watch_gross_cap: float = 0.75
    severe_gross_cap: float = 0.50

    def __post_init__(self) -> None:
        if not isinstance(self.severe_default_fraction, Fraction):
            raise TypeError("CASCADE_DEFAULT_THRESHOLD_FRACTION_REQUIRED")
        if not isinstance(self.severe_unpaid_fraction, Fraction):
            raise TypeError("CASCADE_UNPAID_THRESHOLD_FRACTION_REQUIRED")
        if not Fraction(0) < self.severe_default_fraction <= Fraction(1):
            raise ValueError("CASCADE_DEFAULT_THRESHOLD_OUT_OF_RANGE")
        if not Fraction(0) < self.severe_unpaid_fraction <= Fraction(1):
            raise ValueError("CASCADE_UNPAID_THRESHOLD_OUT_OF_RANGE")
        for field_name in ("watch_gross_cap", "severe_gross_cap"):
            value = float(getattr(self, field_name))
            if not np.isfinite(value) or not 0.0 < value <= 1.5:
                raise ValueError(f"CASCADE_{field_name.upper()}_OUT_OF_RANGE")
        if self.severe_gross_cap > self.watch_gross_cap:
            raise ValueError("CASCADE_SEVERE_CAP_MUST_NOT_EXCEED_WATCH_CAP")


@dataclass(frozen=True, slots=True)
class FinancialCascadeBundle:
    scenario_id: str
    scenario_identity: str
    bundle_identity: str
    institution_ids: tuple[str, ...]
    nominal_obligations: Fraction
    shock_default_count: int
    shock_unpaid_obligations: Fraction
    shock_default_fraction: Fraction
    shock_unpaid_fraction: Fraction
    non_unique_states: tuple[str, ...]
    decision: str
    preferred_intervention_id: str | None
    claim_boundary: str = CLAIM_BOUNDARY

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("CASCADE_SCENARIO_ID_REQUIRED")
        for value, code in (
            (self.scenario_identity, "CASCADE_SCENARIO_IDENTITY_INVALID"),
            (self.bundle_identity, "CASCADE_BUNDLE_IDENTITY_INVALID"),
        ):
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(code)
        if not 2 <= len(self.institution_ids) <= 10:
            raise ValueError("CASCADE_INSTITUTION_COUNT_OUT_OF_RANGE")
        if len(set(self.institution_ids)) != len(self.institution_ids):
            raise ValueError("CASCADE_DUPLICATE_INSTITUTION")
        if self.nominal_obligations <= 0:
            raise ValueError("CASCADE_NOMINAL_OBLIGATIONS_REQUIRED")
        if self.shock_default_count < 0:
            raise ValueError("CASCADE_DEFAULT_COUNT_INVALID")
        if self.shock_unpaid_obligations < 0:
            raise ValueError("CASCADE_UNPAID_OBLIGATIONS_INVALID")
        if self.claim_boundary != CLAIM_BOUNDARY:
            raise ValueError("CASCADE_CLAIM_BOUNDARY_INVALID")


@dataclass(frozen=True, slots=True)
class FinancialCascadeObservation:
    """One PIT-available cascade observation.

    ``effective_date`` is the first portfolio date allowed to consume the bundle.
    ``source_as_of_utc`` and ``available_at_utc`` preserve source/knowledge lineage.
    """

    effective_date: str
    source_as_of_utc: str
    available_at_utc: str
    bundle: FinancialCascadeBundle

    def __post_init__(self) -> None:
        try:
            effective = pd.Timestamp(self.effective_date)
            source = pd.Timestamp(self.source_as_of_utc)
            available = pd.Timestamp(self.available_at_utc)
        except (TypeError, ValueError) as exc:
            raise ValueError("CASCADE_OBSERVATION_TIMESTAMP_INVALID") from exc
        if effective.tzinfo is not None or effective != effective.normalize():
            raise ValueError("CASCADE_EFFECTIVE_DATE_MUST_BE_NAIVE_DATE")
        if self.effective_date != effective.date().isoformat():
            raise ValueError("CASCADE_EFFECTIVE_DATE_NOT_CANONICAL")
        if source.tzinfo is None or available.tzinfo is None:
            raise ValueError("CASCADE_SOURCE_AND_AVAILABLE_TIMESTAMPS_MUST_BE_TZ_AWARE")
        source_utc = source.tz_convert("UTC")
        available_utc = available.tz_convert("UTC")
        if available_utc < source_utc:
            raise ValueError("CASCADE_AVAILABLE_BEFORE_SOURCE_AS_OF")
        if effective <= available_utc.tz_localize(None).normalize():
            raise ValueError("CASCADE_EFFECTIVE_DATE_MUST_FOLLOW_AVAILABILITY_DATE")
        if not isinstance(self.bundle, FinancialCascadeBundle):
            raise TypeError("CASCADE_BUNDLE_TYPE_INVALID")


@dataclass(frozen=True, slots=True)
class FinancialCascadeOverlayResult:
    target_weights: pd.DataFrame
    diagnostics: pd.DataFrame


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FinancialCascadeError("CASCADE_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _load_json_bytes(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise FinancialCascadeError(f"CASCADE_{label}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise FinancialCascadeError(f"CASCADE_{label}_OBJECT_REQUIRED")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FinancialCascadeError("CASCADE_CANONICAL_JSON_INVALID") from exc


def _canonical_file_bytes(value: Any) -> bytes:
    return _canonical_json_bytes(value) + b"\n"


def _canonical_file_matches(raw: bytes, value: Any) -> bool:
    normalized = raw.replace(b"\r\n", b"\n")
    return b"\r" not in normalized and normalized == _canonical_file_bytes(value)


def _sha256_hex(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _identity(value: Mapping[str, Any]) -> str:
    return _sha256_hex(_canonical_json_bytes(dict(value)))


def _fraction(value: object, *, field: str) -> Fraction:
    if not isinstance(value, Mapping) or set(value) != {"numerator", "denominator"}:
        raise FinancialCascadeError(f"CASCADE_{field}_RATIONAL_INVALID")
    numerator = value.get("numerator")
    denominator = value.get("denominator")
    if isinstance(numerator, bool) or not isinstance(numerator, int):
        raise FinancialCascadeError(f"CASCADE_{field}_NUMERATOR_INVALID")
    if isinstance(denominator, bool) or not isinstance(denominator, int) or denominator <= 0:
        raise FinancialCascadeError(f"CASCADE_{field}_DENOMINATOR_INVALID")
    return Fraction(numerator, denominator)


def _require_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FinancialCascadeError(f"CASCADE_{field}_MAPPING_REQUIRED")
    return value


def _require_list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise FinancialCascadeError(f"CASCADE_{field}_LIST_REQUIRED")
    return value


def _validate_clearing_state(
    state: object,
    *,
    expected_scenario_identity: str,
    institution_ids: tuple[str, ...],
    field: str,
) -> tuple[int, Fraction, Fraction]:
    value = _require_mapping(state, field=field)
    if value.get("schema_version") != CLEARING_RESULT_SCHEMA:
        raise FinancialCascadeError(f"CASCADE_{field}_SCHEMA_INVALID")
    if value.get("scenario_identity") != expected_scenario_identity:
        raise FinancialCascadeError(f"CASCADE_{field}_SCENARIO_IDENTITY_MISMATCH")
    if not isinstance(value.get("non_unique"), bool):
        raise FinancialCascadeError(f"CASCADE_{field}_NON_UNIQUE_TYPE_INVALID")

    nominal = _require_mapping(value.get("nominal_obligations"), field=f"{field}_NOMINAL")
    if set(nominal) != set(institution_ids):
        raise FinancialCascadeError(f"CASCADE_{field}_NOMINAL_COVERAGE_INVALID")
    nominal_total = sum(
        (_fraction(amount, field=f"{field}_NOMINAL") for amount in nominal.values()),
        Fraction(0),
    )

    worst_default_count = 0
    worst_unpaid = Fraction(0)
    for bound in ("least", "greatest"):
        outcome = _require_mapping(value.get(bound), field=f"{field}_{bound.upper()}")
        default_count = outcome.get("default_count")
        if isinstance(default_count, bool) or not isinstance(default_count, int):
            raise FinancialCascadeError(f"CASCADE_{field}_{bound.upper()}_DEFAULT_COUNT_INVALID")
        defaults = _require_list(
            outcome.get("defaults"), field=f"{field}_{bound.upper()}_DEFAULTS"
        )
        if default_count != len(defaults) or not set(map(str, defaults)).issubset(
            set(institution_ids)
        ):
            raise FinancialCascadeError(f"CASCADE_{field}_{bound.upper()}_DEFAULTS_INVALID")
        unpaid = _fraction(
            outcome.get("total_unpaid_obligations"),
            field=f"{field}_{bound.upper()}_TOTAL_UNPAID",
        )
        invariants = _require_mapping(
            outcome.get("accounting_invariants"),
            field=f"{field}_{bound.upper()}_INVARIANTS",
        )
        if invariants.get("all_pass") is not True:
            raise FinancialCascadeError(f"CASCADE_{field}_{bound.upper()}_INVARIANTS_FAILED")
        worst_default_count = max(worst_default_count, default_count)
        worst_unpaid = max(worst_unpaid, unpaid)
    return worst_default_count, worst_unpaid, nominal_total


def load_verified_leningrad_bundle(
    bundle_dir: str | Path,
    *,
    expected_bundle_identity: str,
) -> FinancialCascadeBundle:
    """Load one exact externally verified Leningrad choice bundle.

    The expected identity is mandatory and must come from the independent
    Leningrad verifier/custody receipt. Quant verifies tree shape, canonical bytes,
    hashes, identities, internal accounting invariants, and schema consistency; it
    deliberately does not reconstruct the clearing solver.
    """

    if len(expected_bundle_identity) != 64 or any(
        ch not in "0123456789abcdef" for ch in expected_bundle_identity
    ):
        raise FinancialCascadeError("CASCADE_EXPECTED_BUNDLE_IDENTITY_INVALID")

    root = Path(bundle_dir)
    if not root.is_dir() or root.is_symlink():
        raise FinancialCascadeError("CASCADE_BUNDLE_REGULAR_DIRECTORY_REQUIRED")
    entries = list(root.iterdir())
    names = {entry.name for entry in entries}
    if names != _REQUIRED_BUNDLE_FILES:
        raise FinancialCascadeError("CASCADE_BUNDLE_TREE_MISMATCH")
    if any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise FinancialCascadeError("CASCADE_BUNDLE_REGULAR_FILES_REQUIRED")

    raw = {name: (root / name).read_bytes() for name in _REQUIRED_BUNDLE_FILES}
    index = _load_json_bytes(raw["bundle_index.json"], label="BUNDLE_INDEX")
    scenario = _load_json_bytes(raw["scenario.json"], label="SCENARIO")
    comparison = _load_json_bytes(raw["comparison.json"], label="COMPARISON")

    if not _canonical_file_matches(raw["bundle_index.json"], index):
        raise FinancialCascadeError("CASCADE_BUNDLE_INDEX_NOT_CANONICAL")
    if not _canonical_file_matches(raw["scenario.json"], scenario):
        raise FinancialCascadeError("CASCADE_SCENARIO_NOT_CANONICAL")
    if not _canonical_file_matches(raw["comparison.json"], comparison):
        raise FinancialCascadeError("CASCADE_COMPARISON_NOT_CANONICAL")

    if set(index) != {
        "schema_version",
        "scenario_identity",
        "payload_hashes",
        "bundle_identity",
    }:
        raise FinancialCascadeError("CASCADE_BUNDLE_INDEX_FIELDS_INVALID")
    if index.get("schema_version") != CHOICE_BUNDLE_SCHEMA:
        raise FinancialCascadeError("CASCADE_BUNDLE_SCHEMA_UNSUPPORTED")
    payload_hashes = _require_mapping(index.get("payload_hashes"), field="PAYLOAD_HASHES")
    expected_payload_names = {"scenario.json", "comparison.json", "report.md"}
    if set(payload_hashes) != expected_payload_names:
        raise FinancialCascadeError("CASCADE_PAYLOAD_HASH_FIELDS_INVALID")
    observed_payload_hashes = {name: _sha256_hex(raw[name]) for name in expected_payload_names}
    if dict(payload_hashes) != observed_payload_hashes:
        raise FinancialCascadeError("CASCADE_PAYLOAD_HASH_MISMATCH")

    bundle_identity = _identity(
        {
            "kind": "finance-intervention-choice-bundle-identity-v2",
            "payload_hashes": observed_payload_hashes,
        }
    )
    if index.get("bundle_identity") != bundle_identity:
        raise FinancialCascadeError("CASCADE_BUNDLE_IDENTITY_RECONSTRUCTION_FAILED")
    if bundle_identity != expected_bundle_identity:
        raise FinancialCascadeError("CASCADE_EXTERNAL_VERIFIER_IDENTITY_MISMATCH")

    if scenario.get("schema_version") != CHOICE_SCENARIO_SCHEMA:
        raise FinancialCascadeError("CASCADE_SCENARIO_SCHEMA_UNSUPPORTED")
    institutions = _require_list(scenario.get("institutions"), field="INSTITUTIONS")
    institution_ids: list[str] = []
    for row in institutions:
        item = _require_mapping(row, field="INSTITUTION")
        institution_id = item.get("institution_id")
        if not isinstance(institution_id, str) or not institution_id:
            raise FinancialCascadeError("CASCADE_INSTITUTION_ID_INVALID")
        institution_ids.append(institution_id)
    institution_tuple = tuple(institution_ids)
    if not 2 <= len(institution_tuple) <= 10 or len(set(institution_tuple)) != len(
        institution_tuple
    ):
        raise FinancialCascadeError("CASCADE_INSTITUTION_SET_INVALID")

    scenario_identity = _identity(
        {
            "kind": "finance-intervention-choice-scenario-identity-v2",
            "definition": scenario,
        }
    )
    if index.get("scenario_identity") != scenario_identity:
        raise FinancialCascadeError("CASCADE_SCENARIO_IDENTITY_RECONSTRUCTION_FAILED")
    if comparison.get("schema_version") != CHOICE_COMPARISON_SCHEMA:
        raise FinancialCascadeError("CASCADE_COMPARISON_SCHEMA_UNSUPPORTED")
    if comparison.get("scenario_identity") != scenario_identity:
        raise FinancialCascadeError("CASCADE_COMPARISON_SCENARIO_IDENTITY_MISMATCH")
    if comparison.get("scenario_id") != scenario.get("scenario_id"):
        raise FinancialCascadeError("CASCADE_SCENARIO_ID_MISMATCH")

    baseline_defaults, baseline_unpaid, baseline_nominal = _validate_clearing_state(
        comparison.get("baseline"),
        expected_scenario_identity=scenario_identity,
        institution_ids=institution_tuple,
        field="BASELINE",
    )
    shock_defaults, shock_unpaid, shock_nominal = _validate_clearing_state(
        comparison.get("shock"),
        expected_scenario_identity=scenario_identity,
        institution_ids=institution_tuple,
        field="SHOCK",
    )
    if baseline_nominal != shock_nominal:
        raise FinancialCascadeError("CASCADE_NOMINAL_OBLIGATION_DRIFT")
    if baseline_defaults < 0 or baseline_unpaid < 0:
        raise FinancialCascadeError("CASCADE_BASELINE_METRICS_INVALID")

    candidates = _require_mapping(comparison.get("candidates"), field="CANDIDATES")
    scenario_candidates = _require_list(
        scenario.get("candidate_interventions"), field="SCENARIO_CANDIDATES"
    )
    candidate_ids = tuple(
        str(_require_mapping(row, field="SCENARIO_CANDIDATE").get("intervention_id"))
        for row in scenario_candidates
    )
    if len(candidate_ids) != 2 or set(candidates) != set(candidate_ids):
        raise FinancialCascadeError("CASCADE_CANDIDATE_SET_MISMATCH")
    for candidate_id, candidate_value in candidates.items():
        candidate = _require_mapping(candidate_value, field="CANDIDATE")
        if candidate.get("intervention_id") != candidate_id:
            raise FinancialCascadeError("CASCADE_CANDIDATE_ID_MISMATCH")
        _validate_clearing_state(
            candidate.get("clearing"),
            expected_scenario_identity=scenario_identity,
            institution_ids=institution_tuple,
            field=f"CANDIDATE_{candidate_id}",
        )

    decision = comparison.get("decision")
    if decision not in {
        "candidate_preferred",
        "tie",
        "trade_off",
        "ranking_unstable_across_extrema",
    }:
        raise FinancialCascadeError("CASCADE_DECISION_INVALID")
    preferred = comparison.get("preferred_intervention_id")
    if preferred is not None and preferred not in candidates:
        raise FinancialCascadeError("CASCADE_PREFERRED_INTERVENTION_INVALID")
    stable = comparison.get("ranking_stable_across_extrema")
    if not isinstance(stable, bool):
        raise FinancialCascadeError("CASCADE_RANKING_STABILITY_TYPE_INVALID")
    non_unique_states = tuple(
        str(value)
        for value in _require_list(
            comparison.get("non_unique_states"), field="NON_UNIQUE_STATES"
        )
    )

    default_fraction = Fraction(shock_defaults, len(institution_tuple))
    unpaid_fraction = shock_unpaid / shock_nominal
    return FinancialCascadeBundle(
        scenario_id=str(scenario.get("scenario_id") or ""),
        scenario_identity=scenario_identity,
        bundle_identity=bundle_identity,
        institution_ids=institution_tuple,
        nominal_obligations=shock_nominal,
        shock_default_count=shock_defaults,
        shock_unpaid_obligations=shock_unpaid,
        shock_default_fraction=default_fraction,
        shock_unpaid_fraction=unpaid_fraction,
        non_unique_states=non_unique_states,
        decision=str(decision),
        preferred_intervention_id=(str(preferred) if preferred is not None else None),
    )


def classify_financial_cascade(
    bundle: FinancialCascadeBundle,
    *,
    policy: FinancialCascadePolicy | None = None,
) -> CascadeRiskState:
    """Classify shock severity without consuming intervention ranking."""

    if not isinstance(bundle, FinancialCascadeBundle):
        raise TypeError("CASCADE_BUNDLE_TYPE_INVALID")
    active = policy or FinancialCascadePolicy()
    if (
        bundle.non_unique_states
        or bundle.shock_default_fraction >= active.severe_default_fraction
        or bundle.shock_unpaid_fraction >= active.severe_unpaid_fraction
    ):
        return CascadeRiskState.SEVERE
    if bundle.shock_default_count > 0 or bundle.shock_unpaid_obligations > 0:
        return CascadeRiskState.WATCH
    return CascadeRiskState.CLEAR


def build_financial_cascade_overlay(
    observations: Iterable[FinancialCascadeObservation],
    index: pd.Index,
    *,
    policy: FinancialCascadePolicy | None = None,
) -> pd.DataFrame:
    """Project PIT observations to a daily cap series with no backfill."""

    if not isinstance(index, pd.Index):
        raise TypeError("CASCADE_INDEX_REQUIRED")
    dates = pd.DatetimeIndex(index)
    if dates.tz is not None:
        raise FinancialCascadeError("CASCADE_INDEX_MUST_BE_TIMEZONE_NAIVE")
    if dates.hasnans or not dates.is_monotonic_increasing or dates.has_duplicates:
        raise FinancialCascadeError("CASCADE_INDEX_MUST_BE_SORTED_UNIQUE_DATES")
    active = policy or FinancialCascadePolicy()
    rows: list[dict[str, object]] = []
    seen_dates: set[str] = set()
    for observation in observations:
        if not isinstance(observation, FinancialCascadeObservation):
            raise TypeError("CASCADE_OBSERVATION_TYPE_INVALID")
        if observation.effective_date in seen_dates:
            raise FinancialCascadeError("CASCADE_DUPLICATE_EFFECTIVE_DATE")
        seen_dates.add(observation.effective_date)
        state = classify_financial_cascade(observation.bundle, policy=active)
        cap = (
            active.severe_gross_cap
            if state is CascadeRiskState.SEVERE
            else active.watch_gross_cap
            if state is CascadeRiskState.WATCH
            else np.nan
        )
        rows.append(
            {
                "effective_date": pd.Timestamp(observation.effective_date),
                "cascade_state": state.value,
                "gross_exposure_cap": cap,
                "scenario_identity": observation.bundle.scenario_identity,
                "bundle_identity": observation.bundle.bundle_identity,
                "source_as_of_utc": observation.source_as_of_utc,
                "available_at_utc": observation.available_at_utc,
            }
        )

    overlay = pd.DataFrame(index=dates)
    overlay.index.name = dates.name
    overlay["cascade_state"] = CascadeRiskState.UNAVAILABLE.value
    overlay["gross_exposure_cap"] = np.nan
    overlay["scenario_identity"] = None
    overlay["bundle_identity"] = None
    overlay["source_as_of_utc"] = None
    overlay["available_at_utc"] = None
    if not rows:
        return overlay

    source = pd.DataFrame(rows).sort_values("effective_date", kind="mergesort")
    # Pandas may construct scalar observation dates at microsecond precision while
    # a canonical portfolio calendar remains nanosecond precision. merge_asof
    # requires exact dtype equality, so bind observations to the admitted calendar
    # dtype before projection rather than weakening the date comparison.
    source["effective_date"] = pd.to_datetime(source["effective_date"]).astype(
        dates.dtype
    )
    projected = pd.merge_asof(
        pd.DataFrame({"date": dates}),
        source,
        left_on="date",
        right_on="effective_date",
        direction="backward",
        allow_exact_matches=True,
    ).set_index("date")
    projected.index.name = dates.name
    projected["cascade_state"] = projected["cascade_state"].fillna(
        CascadeRiskState.UNAVAILABLE.value
    )
    return projected[
        [
            "cascade_state",
            "gross_exposure_cap",
            "scenario_identity",
            "bundle_identity",
            "source_as_of_utc",
            "available_at_utc",
        ]
    ]


def apply_financial_cascade_cap(
    target_weights: pd.DataFrame,
    overlay: pd.DataFrame,
) -> FinancialCascadeOverlayResult:
    """Scale gross exposure down only; preserve names, signs, and proportions."""

    if not isinstance(target_weights, pd.DataFrame) or not isinstance(
        overlay, pd.DataFrame
    ):
        raise TypeError("CASCADE_WEIGHTS_AND_OVERLAY_DATAFRAMES_REQUIRED")
    if target_weights.empty:
        empty_diag = pd.DataFrame(
            columns=[
                "baseline_gross_exposure",
                "gross_exposure_cap",
                "scale_factor",
                "challenger_gross_exposure",
                "cascade_state",
                "bundle_identity",
                "scenario_identity",
            ],
            index=target_weights.index,
        )
        return FinancialCascadeOverlayResult(target_weights.copy(), empty_diag)
    numeric = target_weights.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
        raise FinancialCascadeError("CASCADE_TARGET_WEIGHTS_NON_FINITE")
    if not numeric.index.equals(overlay.index):
        raise FinancialCascadeError("CASCADE_OVERLAY_INDEX_MISMATCH")
    required = {"cascade_state", "gross_exposure_cap", "bundle_identity", "scenario_identity"}
    if not required.issubset(overlay.columns):
        raise FinancialCascadeError("CASCADE_OVERLAY_COLUMNS_MISSING")

    baseline_gross = numeric.abs().sum(axis=1)
    cap = pd.to_numeric(overlay["gross_exposure_cap"], errors="coerce")
    finite_cap = cap.notna()
    if ((cap[finite_cap] <= 0.0) | (~np.isfinite(cap[finite_cap]))).any():
        raise FinancialCascadeError("CASCADE_GROSS_CAP_INVALID")
    scale = pd.Series(1.0, index=numeric.index, dtype=float)
    constrained = finite_cap & (baseline_gross > cap) & (baseline_gross > 0.0)
    scale.loc[constrained] = cap.loc[constrained] / baseline_gross.loc[constrained]
    challenger = numeric.mul(scale, axis=0)
    challenger_gross = challenger.abs().sum(axis=1)

    diagnostics = pd.DataFrame(
        {
            "baseline_gross_exposure": baseline_gross,
            "gross_exposure_cap": cap,
            "scale_factor": scale,
            "challenger_gross_exposure": challenger_gross,
            "cascade_state": overlay["cascade_state"].astype(str),
            "bundle_identity": overlay["bundle_identity"],
            "scenario_identity": overlay["scenario_identity"],
        },
        index=numeric.index,
    )
    return FinancialCascadeOverlayResult(challenger, diagnostics)
