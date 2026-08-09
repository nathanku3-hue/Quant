#!/usr/bin/env python
"""Restartable XpressAPI historical market-candidate acquisition for Lane 2.

This script never produces an A1 historical risk-set receipt.  It captures the
strictly smaller provider object that XpressAPI can bind directly to a historical
``pricingDate``: CIQ company IDs matching a historical primary-exchange market
screen across a complete, separately sourced provider country-code universe.

Authentication is read from an environment variable and is never written to a
plan, raw response, CSV, or receipt.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.aov0.xpressapi_historical_screen import (  # noqa: E402
    XPRESSAPI_SCREEN_MERGED_RECEIPT_SCHEMA,
    XPRESSAPI_SCREENER_ENDPOINT,
    XpressApiHistoricalScreenError,
    build_market_candidate_plan,
    build_part_receipt,
    merge_market_candidate_parts,
    request_hash,
    sha256_file,
    validate_result_set,
)


DEFAULT_TOKEN_ENV = "SPGLOBAL_XPRESSAPI_TOKEN"


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    _atomic_write_text(path, frame.to_csv(index=False, lineterminator="\n"))


def _require_absent(paths: list[Path]) -> None:
    existing = [path.as_posix() for path in paths if path.exists()]
    if existing:
        raise FileExistsError("refuse_existing:" + ",".join(existing))


def _load_single_column(path: Path, column: str) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    if column not in frame.columns:
        raise ValueError(f"source_column_missing:{column}")
    values = [str(value).strip() for value in frame[column] if str(value).strip()]
    if not values:
        raise ValueError(f"source_column_empty:{column}")
    if len(values) != len(set(value.upper() for value in values)):
        raise ValueError(f"source_column_duplicate:{column}")
    return values


def _source_binding(path: Path, *, source_id: str) -> dict[str, Any]:
    if not source_id.strip():
        raise ValueError("source_id_required")
    return {
        "source_id": source_id.strip(),
        "name": path.name,
        "path": path.resolve().as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def command_plan(args: argparse.Namespace) -> int:
    country_path = args.country_codes.resolve()
    exchange_path = args.primary_exchanges.resolve()
    out = args.out.resolve()
    _require_absent([out])
    countries = _load_single_column(country_path, args.country_column)
    exchanges = _load_single_column(exchange_path, args.exchange_column)
    plan = build_market_candidate_plan(
        as_of_date=args.as_of_date,
        country_codes=countries,
        primary_exchanges=exchanges,
        country_code_universe_source=_source_binding(
            country_path, source_id=args.country_source_id
        ),
        primary_exchange_source=_source_binding(
            exchange_path, source_id=args.exchange_source_id
        ),
        chunk_size=args.chunk_size,
    )
    payload = dict(plan.payload)
    payload["plan_sha256"] = plan.plan_hash
    _write_json(out, payload)
    # The plan's self hash intentionally excludes the self-referential field.
    print(
        f"XPRESS_SCREEN_PLAN_OK\tREQUESTS={payload['request_count']}\t"
        f"COUNTRIES={payload['country_code_count']}\tASOF={payload['as_of_date']}\t"
        f"PLAN_PAYLOAD_SHA256={plan.plan_hash}\tPATH={out}"
    )
    return 0


def _http_post_json(
    *,
    endpoint: str,
    request_payload: dict[str, Any],
    token: str,
    timeout_seconds: int,
) -> tuple[bytes, int, dict[str, str]]:
    body = json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            "User-Agent": "aov0-lane2-xpressapi-historical-screen/1",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed HTTPS endpoint.
            raw = response.read()
            headers = {
                str(key).lower(): str(value)
                for key, value in response.headers.items()
                if str(key).lower() in {"content-type", "date", "x-correlation-id", "correlation-id"}
            }
            return raw, int(response.status), headers
    except HTTPError as exc:
        error_body = exc.read(8192).decode("utf-8", errors="replace")
        # Never include request headers/token. Provider error bodies are bounded.
        raise XpressApiHistoricalScreenError(
            f"xpressapi_http_error:{exc.code}:{error_body}"
        ) from exc
    except URLError as exc:
        raise XpressApiHistoricalScreenError(f"xpressapi_transport_error:{exc.reason}") from exc


def command_capture(args: argparse.Namespace) -> int:
    plan_path = args.plan.resolve()
    out_dir = args.out_dir.resolve()
    if not plan_path.is_file():
        raise FileNotFoundError(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    requests = plan.get("requests") or []
    chunk = int(args.chunk_index)
    if not 0 <= chunk < len(requests):
        raise XpressApiHistoricalScreenError("xpressapi_plan_chunk_index_invalid")
    binding = requests[chunk]
    if request_hash(binding["request"]) != binding.get("request_sha256"):
        raise XpressApiHistoricalScreenError("xpressapi_plan_request_hash_invalid")

    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise XpressApiHistoricalScreenError(
            f"xpressapi_token_missing_in_environment:{args.token_env}"
        )
    if len(token) < 16:
        raise XpressApiHistoricalScreenError("xpressapi_token_value_implausibly_short")

    stem = f"xpress_screen_market_{chunk:03d}_{str(plan['as_of_date']).replace('-', '')}"
    raw_path = out_dir / f"{stem}.raw.json"
    csv_path = out_dir / f"{stem}.csv"
    receipt_path = out_dir / f"{stem}.receipt.json"
    _require_absent([raw_path, csv_path, receipt_path])

    raw_body, status, selected_headers = _http_post_json(
        endpoint=str(plan.get("endpoint") or XPRESSAPI_SCREENER_ENDPOINT),
        request_payload=dict(binding["request"]),
        token=token,
        timeout_seconds=args.timeout_seconds,
    )
    if status != 200:
        raise XpressApiHistoricalScreenError(f"xpressapi_http_status_invalid:{status}")
    try:
        response_payload = json.loads(raw_body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise XpressApiHistoricalScreenError("xpressapi_response_json_invalid") from exc
    validated = validate_result_set(
        response_payload,
        request_payload=binding["request"],
    )

    # Raw provider body lands before normalized/receipt, all atomically. No auth
    # header or token is persisted anywhere.
    _atomic_write_bytes(raw_path, raw_body)
    _write_csv(csv_path, validated.frame)
    receipt = build_part_receipt(
        plan_path=plan_path,
        plan=plan,
        chunk_index=chunk,
        raw_response_path=raw_path,
        normalized_csv_path=csv_path,
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    receipt["http_status"] = status
    receipt["response_headers_allowlisted"] = selected_headers
    receipt["token_environment_variable"] = args.token_env
    receipt["token_value_persisted"] = False
    _write_json(receipt_path, receipt)
    print(
        f"XPRESS_SCREEN_PART_OK\tCHUNK={chunk}\tROWS={len(validated.frame)}\t"
        f"RAW_SHA256={sha256_file(raw_path)}\tPATH={receipt_path}"
    )
    return 0


def command_merge(args: argparse.Namespace) -> int:
    plan_path = args.plan.resolve()
    out_csv = args.out_csv.resolve()
    out_receipt = args.out_receipt.resolve()
    _require_absent([out_csv, out_receipt])
    receipt_paths = [path.resolve() for path in args.part_receipt]
    frame, metadata = merge_market_candidate_parts(
        plan_path=plan_path,
        part_receipt_paths=receipt_paths,
    )
    _write_csv(out_csv, frame)
    metadata = dict(metadata)
    metadata["schema_version"] = XPRESSAPI_SCREEN_MERGED_RECEIPT_SCHEMA
    metadata["merged_csv_name"] = out_csv.name
    metadata["merged_csv_sha256"] = sha256_file(out_csv)
    metadata["merged_csv_bytes"] = out_csv.stat().st_size
    metadata["authorization_material_persisted"] = False
    _write_json(out_receipt, metadata)
    print(
        f"XPRESS_SCREEN_MERGE_OK\tROWS={len(frame)}\tPARTS={len(receipt_paths)}\t"
        f"CSV_SHA256={sha256_file(out_csv)}\tPATH={out_receipt}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--as-of-date", required=True)
    plan.add_argument("--country-codes", type=Path, required=True)
    plan.add_argument("--country-column", default="countryCode")
    plan.add_argument("--country-source-id", required=True)
    plan.add_argument("--primary-exchanges", type=Path, required=True)
    plan.add_argument("--exchange-column", default="primaryExchange")
    plan.add_argument("--exchange-source-id", required=True)
    plan.add_argument("--chunk-size", type=int, default=50)
    plan.add_argument("--out", type=Path, required=True)
    plan.set_defaults(func=command_plan)

    capture = sub.add_parser("capture")
    capture.add_argument("--plan", type=Path, required=True)
    capture.add_argument("--chunk-index", type=int, required=True)
    capture.add_argument("--out-dir", type=Path, required=True)
    capture.add_argument("--token-env", default=DEFAULT_TOKEN_ENV)
    capture.add_argument("--timeout-seconds", type=int, default=60)
    capture.set_defaults(func=command_capture)

    merge = sub.add_parser("merge")
    merge.add_argument("--plan", type=Path, required=True)
    merge.add_argument("--part-receipt", type=Path, action="append", required=True)
    merge.add_argument("--out-csv", type=Path, required=True)
    merge.add_argument("--out-receipt", type=Path, required=True)
    merge.set_defaults(func=command_merge)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
