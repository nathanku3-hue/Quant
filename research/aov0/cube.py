"""Minimal PIT vertical cube for AOV-0 only."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import (
    AOV0Contract,
    DEFAULT_CONTRACT,
    normalize_security_id,
    validate_contract,
)


CUBE_SCHEMA = "vertical_cube_slice_v0"
REQUIRED_COLUMNS = (
    "date",
    "security_id",
    "valid_at",
    "known_at",
    "total_return",
    "realized_vol",
    "dollar_volume",
    "adv20",
    "quality",
    "trend_fast",
    "trend_slow",
    "exit_capacity",
    "regime",
    "uncertainty",
)


@dataclass(frozen=True)
class VerticalCube:
    frame: pd.DataFrame
    cube_hash: str
    source_hash: str
    formula_hash: str
    contract_hash: str


def build_vertical_cube(
    primitives: pd.DataFrame,
    *,
    computed_at: str,
    contract: AOV0Contract = DEFAULT_CONTRACT,
) -> VerticalCube:
    validate_contract(contract)
    missing = [column for column in REQUIRED_COLUMNS if column not in primitives.columns]
    if missing:
        raise ValueError(f"aov0_cube_missing_columns:{','.join(missing)}")
    if primitives.empty:
        raise ValueError("aov0_cube_empty")

    working = primitives.loc[:, REQUIRED_COLUMNS].copy()
    working["date"] = pd.to_datetime(working["date"], errors="raise").dt.normalize()
    working["valid_at"] = pd.to_datetime(working["valid_at"], utc=True, errors="raise")
    working["known_at"] = pd.to_datetime(working["known_at"], utc=True, errors="raise")
    computed_ts = pd.Timestamp(computed_at)
    if computed_ts.tzinfo is None:
        computed_ts = computed_ts.tz_localize("UTC")
    else:
        computed_ts = computed_ts.tz_convert("UTC")

    try:
        working["security_id"] = working["security_id"].map(normalize_security_id)
    except ValueError as exc:
        raise ValueError("aov0_cube_ciq_security_id_required") from exc
    if working.duplicated(["date", "security_id"]).any():
        raise ValueError("aov0_cube_duplicate_date_security_id")

    numeric_columns = (
        "total_return",
        "realized_vol",
        "dollar_volume",
        "adv20",
        "quality",
        "trend_fast",
        "trend_slow",
        "exit_capacity",
        "regime",
        "uncertainty",
    )
    for column in numeric_columns:
        working[column] = pd.to_numeric(working[column], errors="coerce")
        if working[column].isna().any() or not np.isfinite(working[column].to_numpy(dtype=float)).all():
            raise ValueError(f"aov0_cube_non_finite:{column}")
    if (working["realized_vol"] <= 0).any() or (working["adv20"] <= 0).any():
        raise ValueError("aov0_cube_positive_scale_required")
    if (working["dollar_volume"] < 0).any():
        raise ValueError("aov0_cube_dollar_volume_negative")
    if not working["exit_capacity"].between(0, 1).all():
        raise ValueError("aov0_cube_exit_capacity_out_of_bounds")
    if not working["regime"].between(-1, 1).all():
        raise ValueError("aov0_cube_regime_out_of_bounds")
    if not working["uncertainty"].between(0, 1).all():
        raise ValueError("aov0_cube_uncertainty_out_of_bounds")
    if (working["valid_at"] > working["known_at"]).any():
        raise ValueError("aov0_cube_valid_after_known")
    if (working["known_at"] > computed_ts).any():
        raise ValueError("aov0_cube_future_knowledge")

    source_hash = _frame_sha256(working)
    pressure = (
        np.sign(working["total_return"])
        * np.minimum(np.abs(working["total_return"]) / working["realized_vol"], 3.0)
        * (working["dollar_volume"] / working["adv20"])
    )
    working["F_proxy"] = (
        working.assign(_pressure=pressure)
        .groupby("date", sort=False)["_pressure"]
        .transform(_robust_z)
        .clip(-8.0, 8.0)
    )
    working = working.sort_values(["security_id", "date"]).reset_index(drop=True)
    working["C_proxy"] = (
        working.groupby("security_id", sort=False)["F_proxy"]
        .transform(lambda values: values.abs().ewm(span=20, adjust=False, min_periods=1).mean())
    )
    working["Q"] = working["quality"].clip(-3.0, 3.0) / 3.0
    working["M"] = ((working["trend_fast"] + working["trend_slow"]) / 2.0).clip(-3.0, 3.0) / 3.0
    working["L"] = working["exit_capacity"]
    working["R"] = working["regime"]
    working["U"] = working["uncertainty"]
    working["computed_at"] = computed_ts.isoformat()
    working["model_available_at"] = computed_ts.isoformat()
    working["source_hash"] = source_hash
    formula_hash = domain_hash(
        "AOV0:CUBE_FORMULAS:V1",
        {
            "f_proxy": contract.f_proxy_formula,
            "c_proxy": contract.c_proxy_formula,
            "Q": "clip(quality,-3,3)/3",
            "M": "clip(mean(trend_fast,trend_slow),-3,3)/3",
            "L": "bounded_exit_capacity_[0,1]",
            "R": "bounded_regime_[-1,1]",
            "U": "bounded_uncertainty_[0,1]",
        },
    )
    working["formula_hash"] = formula_hash
    working["contract_hash"] = contract.contract_hash
    output_columns = [
        "date",
        "security_id",
        "valid_at",
        "known_at",
        "computed_at",
        "model_available_at",
        "Q",
        "M",
        "F_proxy",
        "C_proxy",
        "L",
        "R",
        "U",
        "source_hash",
        "formula_hash",
        "contract_hash",
    ]
    output = working[output_columns].sort_values(["date", "security_id"]).reset_index(drop=True)
    cube_hash = _frame_sha256(output)
    return VerticalCube(
        frame=output,
        cube_hash=cube_hash,
        source_hash=source_hash,
        formula_hash=formula_hash,
        contract_hash=contract.contract_hash,
    )


def _robust_z(values: pd.Series) -> pd.Series:
    median = float(values.median())
    deviations = (values - median).abs()
    mad = float(deviations.median())
    if not np.isfinite(mad) or mad <= 1e-12:
        return pd.Series(0.0, index=values.index, dtype=float)
    return (values - median) / (1.4826 * mad)


def _frame_sha256(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(str(frame.shape).encode("utf-8"))
    digest.update("|".join(str(column) for column in frame.columns).encode("utf-8"))
    digest.update("|".join(str(dtype) for dtype in frame.dtypes).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy(dtype="uint64").tobytes())
    return digest.hexdigest()
