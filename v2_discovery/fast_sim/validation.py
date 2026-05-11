from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from data.provenance import compute_sha256
from v2_discovery.fast_sim.schemas import ProxyBoundaryError


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    label: str,
) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ProxyBoundaryError(f"{label}: missing required column(s): {', '.join(missing)}")


def validate_no_nulls(df: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    for column in columns:
        validate_required_columns(df, (column,), label)
        mask = df[column].isna()
        if mask.any():
            _raise_bad_value_error(label, column, mask, ("nan",))


def validate_finite_numeric(
    df: pd.DataFrame,
    columns: Iterable[str],
    label: str,
) -> None:
    for column in columns:
        validate_required_columns(df, (column,), label)
        numeric = pd.to_numeric(df[column], errors="coerce")
        values = numeric.to_numpy(dtype="float64", na_value=np.nan)
        mask_values = ~np.isfinite(values)
        if mask_values.any():
            mask = pd.Series(mask_values, index=df.index)
            classes = _bad_numeric_classes(values[mask_values])
            _raise_bad_value_error(label, column, mask, classes)


def validate_positive_numeric(
    df: pd.DataFrame,
    columns: Iterable[str],
    label: str,
) -> None:
    validate_finite_numeric(df, columns, label)
    for column in columns:
        numeric = pd.to_numeric(df[column], errors="coerce")
        mask = numeric <= 0
        if mask.any():
            _raise_bad_value_error(label, column, mask, ("non_positive",))


def validate_manifest_reconciles(
    df: pd.DataFrame,
    manifest: Mapping[str, Any],
    label: str,
    *,
    file_path: str | Path | None = None,
    date_col: str = "date",
) -> None:
    if not isinstance(manifest, Mapping):
        raise ProxyBoundaryError(f"{label}: manifest metadata must be a mapping")

    if "row_count" in manifest:
        expected_row_count = _coerce_int(manifest.get("row_count"), label, "row_count")
        if expected_row_count != len(df):
            raise ProxyBoundaryError(
                f"{label}: manifest row_count mismatch; "
                f"expected={expected_row_count} actual={len(df)}"
            )

    date_range = manifest.get("date_range")
    if isinstance(date_range, Mapping) and date_col in df.columns:
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        if parsed_dates.isna().any():
            _raise_bad_value_error(label, date_col, parsed_dates.isna(), ("nan",))
        if len(parsed_dates) > 0:
            actual_start = parsed_dates.min().strftime("%Y-%m-%d")
            actual_end = parsed_dates.max().strftime("%Y-%m-%d")
        else:
            actual_start = None
            actual_end = None
        expected_start = _clean_optional_date(date_range.get("start"))
        expected_end = _clean_optional_date(date_range.get("end"))
        if expected_start != actual_start:
            raise ProxyBoundaryError(
                f"{label}: manifest date_range.start mismatch; "
                f"expected={expected_start} actual={actual_start}"
            )
        if expected_end != actual_end:
            raise ProxyBoundaryError(
                f"{label}: manifest date_range.end mismatch; "
                f"expected={expected_end} actual={actual_end}"
            )

    expected_sha = str(manifest.get("sha256", "")).strip()
    if expected_sha and file_path is not None:
        actual_sha = compute_sha256(file_path)
        if expected_sha != actual_sha:
            raise ProxyBoundaryError(f"{label}: manifest sha256 mismatch")

    expected_columns = _schema_columns(manifest)
    if expected_columns is not None:
        actual_columns = list(df.columns)
        if expected_columns != actual_columns:
            raise ProxyBoundaryError(
                f"{label}: manifest schema columns mismatch; "
                f"expected={expected_columns} actual={actual_columns}"
            )


def _bad_numeric_classes(values: np.ndarray) -> tuple[str, ...]:
    classes: list[str] = []
    if np.isnan(values).any():
        classes.append("nan")
    if np.isposinf(values).any():
        classes.append("+inf")
    if np.isneginf(values).any():
        classes.append("-inf")
    return tuple(classes)


def _raise_bad_value_error(
    label: str,
    column: str,
    mask: pd.Series,
    classes: Iterable[str],
) -> None:
    bad_indexes = [str(index) for index in mask[mask].index[:5].tolist()]
    class_text = ", ".join(classes)
    raise ProxyBoundaryError(
        f"{label}: column {column} has bad values; "
        f"bad row count={int(mask.sum())}; "
        f"first bad row indexes={bad_indexes}; "
        f"bad value class: {class_text}"
    )


def _schema_columns(manifest: Mapping[str, Any]) -> list[str] | None:
    schema = manifest.get("schema")
    if isinstance(schema, Mapping) and isinstance(schema.get("columns"), (list, tuple)):
        return [str(column) for column in schema["columns"]]
    if isinstance(schema, (list, tuple)):
        return [str(column) for column in schema]
    schema_columns = manifest.get("schema_columns")
    if isinstance(schema_columns, (list, tuple)):
        return [str(column) for column in schema_columns]
    return None


def _coerce_int(value: Any, label: str, field: str) -> int:
    if isinstance(value, bool):
        raise ProxyBoundaryError(f"{label}: manifest {field} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ProxyBoundaryError(f"{label}: manifest {field} must be an integer") from exc


def _clean_optional_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
