"""Fetch and admit direct New York Fed SOFR for the AOV-0 current cut.

The network path is hard-gated until 15:00 America/New_York. The raw response
bytes are hash-bound before an atomic Parquet/receipt publication. The local
retrieval timestamp is deliberately used as conservative ``published_at`` /
knowledge time; this does not claim the provider's exact publication instant.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, time
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4
from zoneinfo import ZoneInfo
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NY_TZ = ZoneInfo("America/New_York")
SOURCE_ID = "NYFED:SOFR"
SOFR_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/last/30.json"
SOFR_GATE = time(15, 0)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("aov0_nyfed_retrieval_time_timezone_required")
    return value.astimezone(UTC)


def _utc_text(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _ensure_after_gate(now: datetime) -> None:
    local = _utc(now).astimezone(NY_TZ)
    if local.time().replace(tzinfo=None) < SOFR_GATE:
        raise RuntimeError(
            "aov0_nyfed_sofr_before_1500_et:"
            f"{local.isoformat()}"
        )


def _parse_rate_rows(payload: object) -> list[dict[str, object]]:
    """Accept the documented NY Fed reference-rate envelope conservatively."""
    if not isinstance(payload, dict):
        raise ValueError("aov0_nyfed_payload_object_required")
    rows = payload.get("refRates")
    if rows is None:
        rows = payload.get("rates")
    if not isinstance(rows, list) or not rows:
        raise ValueError("aov0_nyfed_ref_rates_missing")
    return [row for row in rows if isinstance(row, dict)]


def parse_sofr_payload(raw: bytes, *, retrieved_at: datetime) -> pd.DataFrame:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("aov0_nyfed_json_invalid") from exc
    rows = _parse_rate_rows(payload)
    records: list[dict[str, object]] = []
    for row in rows:
        rate_type = str(row.get("type") or row.get("rateType") or "SOFR").upper().strip()
        if rate_type and "SOFR" not in rate_type:
            continue
        effective = row.get("effectiveDate") or row.get("effective_date") or row.get("date")
        rate = row.get("percentRate")
        if rate is None:
            rate = row.get("rate")
        try:
            effective_date = pd.Timestamp(str(effective)).normalize()
            sofr_percent = float(rate)
        except (TypeError, ValueError):
            continue
        if effective_date.tzinfo is not None:
            effective_date = effective_date.tz_convert("UTC").tz_localize(None).normalize()
        if not np.isfinite(sofr_percent):
            continue
        records.append(
            {
                "effective_date": effective_date,
                # Conservative information-availability time. We intentionally
                # do not fabricate the provider's publication timestamp.
                "published_at": pd.Timestamp(_utc(retrieved_at)),
                "sofr_percent": sofr_percent,
            }
        )
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("aov0_nyfed_no_sofr_rows")
    if frame["effective_date"].duplicated().any():
        # A same-response duplicate with conflicting rates is not safe to pick.
        grouped = frame.groupby("effective_date")["sofr_percent"].nunique(dropna=False)
        if (grouped > 1).any():
            raise ValueError("aov0_nyfed_conflicting_duplicate_effective_date")
        frame = frame.drop_duplicates("effective_date", keep="last")
    return frame.sort_values("effective_date").reset_index(drop=True)


def _network_fetch(url: str) -> tuple[bytes, str]:
    request = Request(
        url,
        headers={"User-Agent": "GodView-AOV0/1.0 (direct NY Fed SOFR intake)"},
        method="GET",
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - host is pinned below
        final_url = str(response.geturl())
        raw = response.read()
    return raw, final_url


def _validate_final_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "markets.newyorkfed.org":
        raise RuntimeError("aov0_nyfed_untrusted_redirect_or_host")


def _atomic_bytes(raw: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        frame.to_parquet(temp, index=False)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_and_admit_sofr(
    *,
    now: datetime | None = None,
    fetcher: Callable[[str], tuple[bytes, str]] = _network_fetch,
    raw_path: Path | None = None,
    parquet_path: Path | None = None,
    receipt_path: Path | None = None,
) -> dict[str, object]:
    retrieved = _utc(now or datetime.now(UTC))
    _ensure_after_gate(retrieved)
    raw, final_url = fetcher(SOFR_URL)
    _validate_final_url(final_url)
    frame = parse_sofr_payload(raw, retrieved_at=retrieved)

    stamp = retrieved.strftime("%Y%m%dT%H%M%SZ")
    raw_out = raw_path or ROOT / f"data/aov0/raw/nyfed_sofr_{stamp}.json"
    parquet_out = parquet_path or ROOT / "data/aov0/current/official_sofr.parquet"
    receipt_out = receipt_path or ROOT / "data/aov0/source_receipts/nyfed_sofr_current.json"
    raw_hash = _sha256_bytes(raw)

    # Publish raw first, then derived Parquet, then the receipt last. A receipt
    # therefore never points at an unpublished derived artifact.
    _atomic_bytes(raw, raw_out)
    _atomic_parquet(frame, parquet_out)
    receipt = {
        "schema_version": "aov0_nyfed_sofr_receipt_v1",
        "source_id": SOURCE_ID,
        "retrieved_at": _utc_text(retrieved),
        "retrieved_at_semantics": "ACTUAL_DIRECT_NYFED_HTTP_RESPONSE_TIME",
        "provider_url": SOFR_URL,
        "final_url": final_url,
        "raw_object_name": raw_out.name,
        "raw_object_sha256": raw_hash,
        "raw_object_bytes": len(raw),
        "published_at_semantics": "CONSERVATIVE_RETRIEVAL_TIME_AS_INFORMATION_AVAILABILITY",
        "rows": int(len(frame)),
        "effective_date_min": frame["effective_date"].min().date().isoformat(),
        "effective_date_max": frame["effective_date"].max().date().isoformat(),
        "output": {
            "path": parquet_out.resolve().as_posix(),
            "sha256": _sha256_file(parquet_out),
            "rows": int(len(frame)),
        },
        "admission_status": "DIRECT_NYFED_SOFR_ADMITTED_AFTER_1500_ET",
    }
    _atomic_json(receipt, receipt_out)
    return {
        "status": receipt["admission_status"],
        "retrieved_at": receipt["retrieved_at"],
        "rows": receipt["rows"],
        "effective_date_max": receipt["effective_date_max"],
        "raw_sha256": raw_hash,
        "parquet": parquet_out.as_posix(),
        "receipt": receipt_out.as_posix(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-out", type=Path)
    parser.add_argument(
        "--parquet-out",
        type=Path,
        default=ROOT / "data/aov0/current/official_sofr.parquet",
    )
    parser.add_argument(
        "--receipt-out",
        type=Path,
        default=ROOT / "data/aov0/source_receipts/nyfed_sofr_current.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(UTC)
    try:
        _ensure_after_gate(now)
    except RuntimeError as exc:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_NYFED_BEFORE_1500_ET",
                    "reason": str(exc),
                    "network_called": False,
                    "financial_alpha_evidence": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    result = fetch_and_admit_sofr(
        now=now,
        raw_path=args.raw_out,
        parquet_path=args.parquet_out,
        receipt_path=args.receipt_out,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
