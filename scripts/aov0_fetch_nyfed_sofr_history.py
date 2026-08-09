"""Fetch a hash-bound historical official New York Fed SOFR series for Lane 2.

The historical AOV comparator uses only an official SOFR whose effective date
strictly precedes the return interval start. The API does not provide a retained
per-observation publication timestamp in this response, so the evidence receipt
states that conservative availability rule explicitly rather than fabricating
one. This source is historical benchmark authority only; it does not replace the
prospective current-cut SOFR receipt.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json"
SOURCE_ID = "NYFED:SOFR:HISTORICAL_SEARCH"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_bytes(raw: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def fetch_history(start: str, end: str) -> tuple[bytes, str]:
    query = urlencode({"startDate": start, "endDate": end, "type": "rate"})
    url = f"{BASE_URL}?{query}"
    request = Request(url, headers={"User-Agent": "GodView-AOV0-Historical-PIT/1.0"}, method="GET")
    with urlopen(request, timeout=30) as response:  # noqa: S310 - host checked below
        final_url = str(response.geturl())
        raw = response.read()
    parsed = urlparse(final_url)
    if parsed.scheme != "https" or parsed.hostname != "markets.newyorkfed.org":
        raise RuntimeError("aov0_historical_sofr_untrusted_redirect_or_host")
    return raw, final_url


def validate_payload(raw: bytes, *, start: str, end: str) -> pd.DataFrame:
    payload = json.loads(raw.decode("utf-8"))
    rows = payload.get("refRates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("aov0_historical_sofr_no_rows")
    frame = pd.DataFrame(rows)
    if "effectiveDate" not in frame.columns or "percentRate" not in frame.columns:
        raise ValueError("aov0_historical_sofr_required_fields_missing")
    frame["effective_date"] = pd.to_datetime(frame["effectiveDate"], errors="raise").dt.normalize()
    frame["sofr_percent"] = pd.to_numeric(frame["percentRate"], errors="raise")
    lower = pd.Timestamp(start).normalize()
    upper = pd.Timestamp(end).normalize()
    frame = frame.loc[frame["effective_date"].between(lower, upper)].copy()
    if frame.empty:
        raise ValueError("aov0_historical_sofr_requested_window_empty")
    conflicts = frame.groupby("effective_date")["sofr_percent"].nunique(dropna=False)
    if (conflicts > 1).any():
        raise ValueError("aov0_historical_sofr_conflicting_effective_date")
    return frame.sort_values("effective_date").drop_duplicates("effective_date", keep="last")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--raw-out", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    args = parser.parse_args()

    retrieved = datetime.now(UTC)
    raw, final_url = fetch_history(args.start, args.end)
    frame = validate_payload(raw, start=args.start, end=args.end)
    _atomic_bytes(raw, args.raw_out)
    receipt = {
        "schema_version": "aov0_historical_nyfed_sofr_receipt_v1",
        "source_id": SOURCE_ID,
        "retrieved_at_utc": retrieved.isoformat().replace("+00:00", "Z"),
        "provider_url": BASE_URL,
        "final_url": final_url,
        "raw_path": args.raw_out.resolve().as_posix(),
        "raw_sha256": _sha256_bytes(raw),
        "raw_bytes": len(raw),
        "row_count": int(len(frame)),
        "effective_date_min": frame["effective_date"].min().date().isoformat(),
        "effective_date_max": frame["effective_date"].max().date().isoformat(),
        "historical_availability_rule": "USE_ONLY_EFFECTIVE_DATE_STRICTLY_BEFORE_RETURN_INTERVAL_START",
        "publication_timestamp_claimed": False,
        "authority_scope": "HISTORICAL_ECONOMIC_CASH_COMPARATOR_ONLY",
        "financial_alpha_evidence": 0,
    }
    _atomic_json(receipt, args.receipt_out)
    print(json.dumps({
        "status": "HISTORICAL_NYFED_SOFR_ADMITTED",
        "rows": len(frame),
        "effective_date_min": receipt["effective_date_min"],
        "effective_date_max": receipt["effective_date_max"],
        "raw_sha256": receipt["raw_sha256"],
        "receipt_sha256": _sha256_file(args.receipt_out),
        "financial_alpha_evidence": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
