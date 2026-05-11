from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.validation import validate_finite_numeric
from v2_discovery.fast_sim.validation import validate_manifest_reconciles
from v2_discovery.fast_sim.validation import validate_no_nulls
from v2_discovery.fast_sim.validation import validate_positive_numeric
from v2_discovery.fast_sim.validation import validate_required_columns


SYNTHETIC_FIXTURE_SCOPE = "v2_proxy_synthetic_g1"
SYNTHETIC_FIXTURE_ROOT = Path("data/fixtures/v2_proxy")
PRICE_COLUMNS = ("date", "symbol", "close")
WEIGHT_COLUMNS = ("date", "symbol", "target_weight")


@dataclass(frozen=True)
class SyntheticProxyFixture:
    manifest: Mapping[str, Any]
    manifest_path: Path
    prices_path: Path
    weights_path: Path
    prices: pd.DataFrame
    weights: pd.DataFrame


def load_synthetic_proxy_fixture(
    manifest_uri: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> SyntheticProxyFixture:
    if not str(manifest_uri).strip():
        raise ProxyBoundaryError("Synthetic fixture manifest is required")
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    manifest_path = _resolve(root, manifest_uri)
    _require_fixture_path(root, manifest_path)
    if not manifest_path.exists():
        raise ProxyBoundaryError(f"Synthetic fixture manifest does not exist: {manifest_uri}")

    manifest = load_manifest(manifest_path)
    _validate_synthetic_manifest_contract(root, manifest)
    extra = manifest.get("extra")
    if not isinstance(extra, Mapping):
        raise ProxyBoundaryError("Synthetic fixture manifest requires extra fixture metadata")
    if extra.get("fixture_scope") != SYNTHETIC_FIXTURE_SCOPE:
        raise ProxyBoundaryError("Synthetic fixture manifest has an invalid fixture scope")

    prices_metadata = extra.get("prices")
    weights_metadata = extra.get("weights")
    prices_path = _verified_fixture_file(root, prices_metadata, "prices")
    weights_path = _verified_fixture_file(root, weights_metadata, "weights")
    prices = _load_prices(prices_path)
    weights = _load_weights(weights_path)
    validate_manifest_reconciles(
        prices,
        _require_metadata_mapping(prices_metadata, "prices"),
        "synthetic prices",
        file_path=prices_path,
    )
    validate_manifest_reconciles(
        weights,
        _require_metadata_mapping(weights_metadata, "weights"),
        "synthetic weights",
        file_path=weights_path,
    )
    artifact_path = _resolve(root, str(manifest.get("artifact_path", "")))
    validate_manifest_reconciles(
        weights,
        manifest,
        "synthetic manifest artifact",
        file_path=artifact_path,
    )
    _validate_price_coverage(prices, weights)
    return SyntheticProxyFixture(
        manifest=manifest,
        manifest_path=manifest_path,
        prices_path=prices_path,
        weights_path=weights_path,
        prices=prices,
        weights=weights,
    )


def _verified_fixture_file(root: Path, payload: Any, label: str) -> Path:
    payload = _require_metadata_mapping(payload, label)
    path_value = payload.get("path")
    expected_hash = str(payload.get("sha256", "")).strip()
    if not path_value or not expected_hash:
        raise ProxyBoundaryError(f"Synthetic fixture manifest requires {label} path and sha256")
    path = _resolve(root, path_value)
    _require_fixture_path(root, path)
    if not path.exists():
        raise ProxyBoundaryError(f"Synthetic fixture {label} file does not exist: {path_value}")
    actual_hash = compute_sha256(path)
    if actual_hash != expected_hash:
        raise ProxyBoundaryError(f"Synthetic fixture {label} hash mismatch")
    return path


def _require_metadata_mapping(payload: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ProxyBoundaryError(f"Synthetic fixture manifest requires {label} metadata")
    return payload


def _validate_synthetic_manifest_contract(root: Path, manifest: Mapping[str, Any]) -> None:
    if manifest.get("provider") != "synthetic_fixture":
        raise ProxyBoundaryError("Synthetic proxy rejects real market data providers")
    if manifest.get("provider_feed") != "prebaked_target_weights":
        raise ProxyBoundaryError("Synthetic proxy requires prebaked target weights")
    if manifest.get("license_scope") != "synthetic_fixture_only":
        raise ProxyBoundaryError("Synthetic proxy rejects non-synthetic license scopes")
    if manifest.get("source_quality") not in {"non_canonical", "rejected"}:
        raise ProxyBoundaryError("Synthetic proxy fixtures cannot be canonical source quality")
    artifact_path = _resolve(root, str(manifest.get("artifact_path", "")))
    _require_fixture_path(root, artifact_path)
    if compute_sha256(artifact_path) != str(manifest.get("sha256", "")).strip():
        raise ProxyBoundaryError("Synthetic fixture manifest artifact hash mismatch")


def _load_prices(path: Path) -> pd.DataFrame:
    prices = pd.read_csv(path, dtype={"date": "string", "symbol": "string"})
    validate_required_columns(prices, PRICE_COLUMNS, "synthetic prices")
    if tuple(prices.columns) != PRICE_COLUMNS:
        raise ProxyBoundaryError("Synthetic prices must have strict columns: date, symbol, close")
    prices = prices.copy()
    prices["date"] = _normalize_dates(prices["date"], "prices.date")
    validate_no_nulls(prices, ("date", "symbol"), "synthetic prices")
    prices["symbol"] = prices["symbol"].str.strip()
    validate_no_nulls(prices, ("date", "symbol"), "synthetic prices")
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    if prices[["date", "symbol"]].duplicated().any():
        raise ProxyBoundaryError("Synthetic prices contain duplicate date/symbol rows")
    validate_no_nulls(prices, ("date", "symbol", "close"), "synthetic prices")
    validate_positive_numeric(prices, ("close",), "synthetic prices")
    if prices["symbol"].eq("").any():
        raise ProxyBoundaryError("Synthetic prices require non-empty symbols and positive prices")
    return prices.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def _load_weights(path: Path) -> pd.DataFrame:
    weights = pd.read_csv(path, dtype={"date": "string", "symbol": "string"})
    validate_required_columns(weights, WEIGHT_COLUMNS, "synthetic weights")
    if tuple(weights.columns) != WEIGHT_COLUMNS:
        raise ProxyBoundaryError(
            "Synthetic proxy accepts prebaked target weights only: date, symbol, target_weight"
    )
    weights = weights.copy()
    weights["date"] = _normalize_dates(weights["date"], "weights.date")
    validate_no_nulls(weights, ("date", "symbol"), "synthetic weights")
    weights["symbol"] = weights["symbol"].str.strip()
    validate_no_nulls(weights, ("date", "symbol"), "synthetic weights")
    weights["target_weight"] = pd.to_numeric(weights["target_weight"], errors="coerce")
    if weights[["date", "symbol"]].duplicated().any():
        raise ProxyBoundaryError("Synthetic weights contain duplicate date/symbol rows")
    validate_no_nulls(weights, ("date", "symbol", "target_weight"), "synthetic weights")
    validate_finite_numeric(weights, ("target_weight",), "synthetic weights")
    if weights["symbol"].eq("").any():
        raise ProxyBoundaryError("Synthetic weights require non-empty symbols and numeric weights")
    return weights.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def _validate_price_coverage(prices: pd.DataFrame, weights: pd.DataFrame) -> None:
    price_keys = set(map(tuple, prices[["date", "symbol"]].to_numpy()))
    weight_keys = set(map(tuple, weights[["date", "symbol"]].to_numpy()))
    missing = sorted(weight_keys - price_keys)
    if missing:
        first_date, first_symbol = missing[0]
        raise ProxyBoundaryError(
            f"Synthetic prices missing row for date={first_date} symbol={first_symbol}"
        )


def _normalize_dates(series: pd.Series, field: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ProxyBoundaryError(f"{field} contains invalid dates")
    return parsed.dt.strftime("%Y-%m-%d")


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _require_fixture_path(root: Path, path: Path) -> None:
    fixture_root = (root / SYNTHETIC_FIXTURE_ROOT).resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(fixture_root)
    except ValueError as exc:
        raise ProxyBoundaryError("Synthetic proxy rejects non-fixture data paths") from exc
