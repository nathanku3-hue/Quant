"""Hash-addressed selective recomputation for the AOV-0 policy vertical."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import AOV0Contract, DEFAULT_CONTRACT
from research.aov0.cube import VerticalCube
from research.aov0.policy import (
    DEFAULT_MUTATION,
    MutationManifest,
    build_child_weights,
    build_parent_weights,
    normalize_rule100_control,
)


@dataclass
class HashDagCache:
    frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    node_hashes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DagRunResult:
    rule100: pd.DataFrame
    parent: pd.DataFrame
    child: pd.DataFrame
    node_hashes: dict[str, str]
    cache_hits: int
    cache_misses: int


def run_policy_dag(
    rule100_weights: pd.DataFrame,
    cube: VerticalCube,
    *,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    mutation: MutationManifest = DEFAULT_MUTATION,
    cache: HashDagCache | None = None,
) -> DagRunResult:
    cache = cache if cache is not None else HashDagCache()
    hits = 0
    misses = 0

    rule100 = normalize_rule100_control(rule100_weights)
    rule_identity = domain_hash(
        "AOV0:DAG:RULE100:V1",
        {"weights_sha256": _frame_hash(rule100), "contract_hash": contract.contract_hash},
    )
    if rule_identity in cache.frames:
        rule100 = cache.frames[rule_identity].copy()
        hits += 1
    else:
        cache.frames[rule_identity] = rule100.copy()
        cache.node_hashes[rule_identity] = _frame_hash(rule100)
        misses += 1

    parent_identity = domain_hash(
        "AOV0:DAG:PARENT:V1",
        {
            "rule_identity": rule_identity,
            "cube_hash": cube.cube_hash,
            "contract_hash": contract.contract_hash,
        },
    )
    if parent_identity in cache.frames:
        parent = cache.frames[parent_identity].copy()
        hits += 1
    else:
        parent = build_parent_weights(rule100, cube, contract=contract)
        cache.frames[parent_identity] = parent.copy()
        cache.node_hashes[parent_identity] = _frame_hash(parent)
        misses += 1

    child_identity = domain_hash(
        "AOV0:DAG:CHILD:V1",
        {
            "parent_identity": parent_identity,
            "cube_hash": cube.cube_hash,
            "mutation_hash": mutation.manifest_hash,
        },
    )
    if child_identity in cache.frames:
        child = cache.frames[child_identity].copy()
        hits += 1
    else:
        child = build_child_weights(parent, cube, mutation=mutation)
        cache.frames[child_identity] = child.copy()
        cache.node_hashes[child_identity] = _frame_hash(child)
        misses += 1

    return DagRunResult(
        rule100=rule100,
        parent=parent,
        child=child,
        node_hashes={
            "rule100": cache.node_hashes[rule_identity],
            "parent": cache.node_hashes[parent_identity],
            "child": cache.node_hashes[child_identity],
        },
        cache_hits=hits,
        cache_misses=misses,
    )


def _frame_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(str(frame.shape).encode("utf-8"))
    digest.update("|".join(str(column) for column in frame.columns).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy(dtype="uint64").tobytes())
    return digest.hexdigest()
