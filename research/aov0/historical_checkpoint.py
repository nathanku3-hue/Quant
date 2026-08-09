"""Exact frozen-AOV historical decision checkpoint for Lane 2.

This module reconstructs a *decision* from legitimately admitted historical PIT
fundamentals plus market rows available no later than the decision target.  It
never accepts post-target market rows and never computes outcomes.  Historical
labels therefore remain structurally separate from the frozen Rule100 / Parent /
Child computation.

The policy path is the incumbent executable path:

    build_ciq_market_slice -> build_vertical_cube -> run_policy_dag

No historical-only policy parameters or compatibility fallbacks exist here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from typing import Any, Iterable, Mapping

import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.ciq_market import (
    DATE_ALIASES,
    ENTITY_ALIASES,
    CiqMarketSlice,
    build_ciq_market_slice,
)
from research.aov0.contracts import DEFAULT_CONTRACT
from research.aov0.cube import VerticalCube, build_vertical_cube
from research.aov0.dag import DagRunResult, run_policy_dag
from research.aov0.policy import DEFAULT_MUTATION


CHECKPOINT_SCHEMA = "aov0_historical_pit_decision_checkpoint_v1"
DECISION_AUTHORITY = "HISTORICAL_PIT_DECISION_ONLY_NO_OUTCOME_AUTHORITY"


@dataclass(frozen=True)
class HistoricalAOVDecisionCheckpoint:
    checkpoint_id: str
    manifest: Mapping[str, Any]
    market_slice: CiqMarketSlice
    cube: VerticalCube
    dag: DagRunResult


class HistoricalCheckpointError(ValueError):
    """Fail-closed historical decision reconstruction error."""


def build_historical_aov_decision_checkpoint(
    *,
    security_master_raw: pd.DataFrame,
    decision_market_raw: pd.DataFrame,
    fundamental_state: pd.DataFrame,
    frozen_entity_ids: Iterable[object],
    target_date: str,
    decision_cut_time: datetime | str | pd.Timestamp,
    source_bindings: Mapping[str, str],
) -> HistoricalAOVDecisionCheckpoint:
    """Build one frozen-AOV historical decision with outcomes absent.

    ``decision_market_raw`` must contain no row after ``target_date``.  Callers
    handling a wider custody object must split it before invoking this function.
    ``source_bindings`` must bind immutable hashes for historical fundamentals,
    primary-security master, and the decision-only market object.
    """

    target = _date(target_date, field="target_date")
    cut = _aware_utc(decision_cut_time, field="decision_cut_time")
    frozen = _frozen_entities(frozen_entity_ids)
    _validate_source_bindings(source_bindings)
    _validate_fundamental_state(fundamental_state, frozen=frozen, target=target, cut=cut)
    _validate_master_membership(security_master_raw, frozen=frozen)
    _validate_decision_market(decision_market_raw, target=target)

    market_slice = build_ciq_market_slice(
        security_master_raw=security_master_raw,
        market_raw=decision_market_raw,
        fundamental_state=fundamental_state,
        admission_time=cut.to_pydatetime(),
        target_date=target.date().isoformat(),
    )
    if market_slice.rule100_targets.index.tolist() != [target]:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_rule100_target_date_invalid")
    if market_slice.metadata.get("historical_rule100_targets_emitted") is not False:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_market_builder_authority_drift")

    cube = build_vertical_cube(
        market_slice.market_features,
        computed_at=cut.isoformat(),
        contract=DEFAULT_CONTRACT,
    )
    dag = run_policy_dag(
        market_slice.rule100_targets,
        cube,
        contract=DEFAULT_CONTRACT,
        mutation=DEFAULT_MUTATION,
    )
    _validate_target_sets(dag)

    admitted_ids = tuple(sorted(str(column) for column in dag.rule100.columns))
    manifest_body: dict[str, Any] = {
        "schema_version": CHECKPOINT_SCHEMA,
        "decision_authority": DECISION_AUTHORITY,
        "target_date": target.date().isoformat(),
        "decision_cut_time": cut.isoformat().replace("+00:00", "Z"),
        "frozen_candidate_entity_count": len(frozen),
        "admitted_security_count": len(admitted_ids),
        "admitted_security_ids": list(admitted_ids),
        "mechanical_exclusion_count": int(len(market_slice.exclusions)),
        "mechanical_exclusion_reasons": _reason_counts(market_slice.exclusions),
        "rule100_sizing_eligible_count": int((dag.rule100.iloc[0] > 0.0).sum()),
        "rule100_risky_gross": format(float(dag.rule100.iloc[0].sum()), ".17g"),
        "contract_hash": DEFAULT_CONTRACT.contract_hash,
        "mutation_hash": DEFAULT_MUTATION.manifest_hash,
        "source_bindings": {str(key): str(source_bindings[key]) for key in sorted(source_bindings)},
        "input_frame_hashes": {
            "security_master_raw": _frame_hash(security_master_raw),
            "decision_market_raw": _frame_hash(decision_market_raw),
            "fundamental_state": _frame_hash(fundamental_state),
        },
        "cube_hash": cube.cube_hash,
        "cube_source_hash": cube.source_hash,
        "cube_formula_hash": cube.formula_hash,
        "policy_node_hashes": dict(dag.node_hashes),
        "target_vector_hashes": {
            "rule100": _frame_hash(dag.rule100),
            "parent": _frame_hash(dag.parent),
            "child": _frame_hash(dag.child),
        },
        "outcome_data_loaded": False,
        "outcome_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    checkpoint_id = domain_hash("AOV0:HISTORICAL_PIT_DECISION_CHECKPOINT:V1", manifest_body)
    manifest = {**manifest_body, "checkpoint_id": checkpoint_id}
    return HistoricalAOVDecisionCheckpoint(
        checkpoint_id=checkpoint_id,
        manifest=manifest,
        market_slice=market_slice,
        cube=cube,
        dag=dag,
    )


def verify_historical_aov_decision_checkpoint(checkpoint: HistoricalAOVDecisionCheckpoint) -> None:
    manifest = dict(checkpoint.manifest)
    if manifest.get("schema_version") != CHECKPOINT_SCHEMA:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_schema_invalid")
    if manifest.get("decision_authority") != DECISION_AUTHORITY:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_authority_invalid")
    if manifest.get("outcome_data_loaded") is not False or manifest.get("outcome_authority") != "NONE":
        raise HistoricalCheckpointError("aov0_historical_checkpoint_outcome_authority_forbidden")
    if manifest.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalCheckpointError("aov0_historical_checkpoint_mutation_authority_forbidden")
    if manifest.get("financial_alpha_evidence") != 0:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_financial_alpha_evidence_invalid")
    supplied = str(manifest.pop("checkpoint_id", ""))
    expected = domain_hash("AOV0:HISTORICAL_PIT_DECISION_CHECKPOINT:V1", manifest)
    if supplied != expected or checkpoint.checkpoint_id != expected:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_hash_mismatch")

    expected_targets = manifest.get("target_vector_hashes") or {}
    actual_targets = {
        "rule100": _frame_hash(checkpoint.dag.rule100),
        "parent": _frame_hash(checkpoint.dag.parent),
        "child": _frame_hash(checkpoint.dag.child),
    }
    if expected_targets != actual_targets:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_target_hash_mismatch")
    if manifest.get("cube_hash") != checkpoint.cube.cube_hash:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_cube_hash_mismatch")


def split_historical_market_custody(
    market_raw: pd.DataFrame,
    *,
    target_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a broad raw custody object before decision reconstruction.

    The first return value is the only frame permitted to enter the decision
    checkpoint.  The second remains outcome-side custody and carries no decision
    authority.
    """

    if not isinstance(market_raw, pd.DataFrame) or market_raw.empty:
        raise HistoricalCheckpointError("aov0_historical_market_raw_required")
    target = _date(target_date, field="target_date")
    date_column = _column_for_aliases(market_raw, DATE_ALIASES, field="market_date")
    dates = pd.to_datetime(market_raw[date_column], errors="raise").dt.normalize()
    decision = market_raw.loc[dates.le(target)].copy().reset_index(drop=True)
    outcome = market_raw.loc[dates.gt(target)].copy().reset_index(drop=True)
    if decision.empty:
        raise HistoricalCheckpointError("aov0_historical_market_decision_partition_empty")
    return decision, outcome


def _validate_fundamental_state(
    state: pd.DataFrame,
    *,
    frozen: tuple[str, ...],
    target: pd.Timestamp,
    cut: pd.Timestamp,
) -> None:
    required = {
        "source_entity_id",
        "known_at",
        "factor_present_count",
        "factor_positive_count",
        "pit_mode",
    }
    if not isinstance(state, pd.DataFrame) or state.empty or not required.issubset(state.columns):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_fundamental_state_invalid")
    entities = tuple(sorted(state["source_entity_id"].fillna("").astype(str).str.strip()))
    if entities != frozen or len(entities) != len(set(entities)):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_frozen_entity_state_mismatch")
    if state["pit_mode"].fillna("").astype(str).str.contains("CURRENT_CUT", case=False).any():
        raise HistoricalCheckpointError("aov0_historical_checkpoint_current_fundamentals_forbidden")
    known = pd.to_datetime(state["known_at"], utc=True, errors="raise", format="mixed")
    if (known > cut).any():
        raise HistoricalCheckpointError("aov0_historical_checkpoint_future_fundamental_knowledge")
    if (known.dt.tz_convert("UTC").dt.date > target.date()).any():
        raise HistoricalCheckpointError("aov0_historical_checkpoint_fundamental_available_after_target_date")


def _validate_master_membership(master: pd.DataFrame, *, frozen: tuple[str, ...]) -> None:
    if not isinstance(master, pd.DataFrame) or master.empty:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_security_master_required")
    entity_column = _column_for_aliases(master, ENTITY_ALIASES, field="master_entity")
    entities = tuple(sorted(master[entity_column].fillna("").astype(str).str.strip()))
    if entities != frozen or len(entities) != len(set(entities)):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_master_frozen_entity_mismatch")


def _validate_decision_market(market: pd.DataFrame, *, target: pd.Timestamp) -> None:
    if not isinstance(market, pd.DataFrame) or market.empty:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_decision_market_required")
    date_column = _column_for_aliases(market, DATE_ALIASES, field="market_date")
    dates = pd.to_datetime(market[date_column], errors="raise").dt.normalize()
    if dates.gt(target).any():
        raise HistoricalCheckpointError("aov0_historical_checkpoint_post_target_market_forbidden")
    if not dates.eq(target).any():
        raise HistoricalCheckpointError("aov0_historical_checkpoint_target_market_missing")


def _validate_target_sets(dag: DagRunResult) -> None:
    frames = (dag.rule100, dag.parent, dag.child)
    if any(frame.empty or len(frame) != 1 for frame in frames):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_single_target_required")
    if not (dag.rule100.index.equals(dag.parent.index) and dag.parent.index.equals(dag.child.index)):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_target_calendar_mismatch")
    if not (dag.rule100.columns.equals(dag.parent.columns) and dag.parent.columns.equals(dag.child.columns)):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_target_asset_set_mismatch")


def _validate_source_bindings(bindings: Mapping[str, str]) -> None:
    required = {"historical_fundamentals", "primary_security_master", "decision_market"}
    if set(bindings) != required:
        raise HistoricalCheckpointError("aov0_historical_checkpoint_source_bindings_invalid")
    for key, digest in bindings.items():
        text = str(digest).strip().lower()
        if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
            raise HistoricalCheckpointError(f"aov0_historical_checkpoint_source_hash_invalid:{key}")


def _frozen_entities(values: Iterable[object]) -> tuple[str, ...]:
    normalized = tuple(sorted(str(value).strip() for value in values))
    if not normalized or any(not value for value in normalized) or len(normalized) != len(set(normalized)):
        raise HistoricalCheckpointError("aov0_historical_checkpoint_frozen_entities_invalid")
    return normalized


def _date(value: object, *, field: str) -> pd.Timestamp:
    parsed = pd.Timestamp(str(value))
    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert("UTC").tz_localize(None)
    parsed = parsed.normalize()
    if str(value) != parsed.date().isoformat():
        raise HistoricalCheckpointError(f"aov0_historical_checkpoint_{field}_date_required")
    return parsed


def _aware_utc(value: datetime | str | pd.Timestamp, *, field: str) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        raise HistoricalCheckpointError(f"aov0_historical_checkpoint_{field}_timezone_required")
    return parsed.tz_convert("UTC")


def _column_for_aliases(frame: pd.DataFrame, aliases: set[str], *, field: str) -> str:
    for column in frame.columns:
        if _token(column) in aliases:
            return str(column)
    raise HistoricalCheckpointError(f"aov0_historical_checkpoint_{field}_column_required")


def _token(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _frame_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(str(frame.shape).encode("utf-8"))
    digest.update("|".join(str(column) for column in frame.columns).encode("utf-8"))
    digest.update("|".join(str(dtype) for dtype in frame.dtypes).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy(dtype="uint64").tobytes())
    return digest.hexdigest()


def _reason_counts(exclusions: pd.DataFrame) -> dict[str, int]:
    if exclusions.empty or "reason" not in exclusions.columns:
        return {}
    counts = exclusions["reason"].fillna("UNKNOWN").astype(str).value_counts().sort_index()
    return {str(reason): int(count) for reason, count in counts.items()}
