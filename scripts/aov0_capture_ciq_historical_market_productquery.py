"""Capture Lane-2 historical market bytes through an existing CIQ Pro web session.

This entrypoint never signs in, signs out, launches, or navigates Capital IQ Pro.
It attaches to an already-running Chromium DevTools target and reuses that page's
authenticated ProductQuery session. Raw parts are hash-bound to the exact
historical security master and are written atomically. ``--resume`` verifies and
reuses complete existing parts instead of re-querying them.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import pandas as pd
import requests
import websockets


SOURCE_ID = "SPCIQPRO:SECURITIES_PRODUCTQUERY"
PART_SCHEMA = "aov0_ciq_productquery_historical_market_part_receipt_v1"
MANIFEST_SCHEMA = "aov0_ciq_productquery_historical_market_capture_manifest_v1"
MARKET_PERSPECTIVE = "321247"
QUERY_IDENTITY_FIELD = "321263"
MI_KEY_FIELD = "322517"
CIQ_ID_FIELD = "322518"
TOTAL_RETURN_FIELD = "322797"
PRICE_FIELD = "324251"
VOLUME_FIELD = "324277"
DATE_SECONDARY_KEY = "sk_557"
TOTAL_RETURN_PERIOD_SECONDARY_KEY = "sk_100"
TOTAL_RETURN_PERIOD = "1D"
EXPECTED_PROVIDER = "S&P Capital IQ Pro authenticated existing web session"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _value(value: object) -> str:
    if value is None:
        return "NA"
    text = str(value).strip()
    if not text or text.upper() in {"NA", "N/A", "NAN", "NULL", "NONE", "KEYERROR"}:
        return "NA"
    return text


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    except BaseException:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


def _atomic_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("market_capture_rows_empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    except BaseException:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


class Cdp:
    def __init__(self, port: int):
        self.port = port
        self.ws = None
        self.next_id = 1

    async def __aenter__(self):
        targets = requests.get(f"http://127.0.0.1:{self.port}/json/list", timeout=5).json()
        page = next(
            (
                target
                for target in targets
                if target.get("type") == "page"
                and "capitaliq.spglobal.com" in target.get("url", "")
            ),
            None,
        )
        if page is None:
            raise RuntimeError("existing_ciq_pro_browser_session_not_found")
        # Modern Chromium rejects a synthetic DevTools Origin unless the browser
        # was launched with an explicit allow-list.  Omitting Origin attaches to
        # the already-running local debugger without changing the CIQ page or its
        # authenticated session.
        self.ws = await websockets.connect(
            page["webSocketDebuggerUrl"],
            max_size=256 * 1024 * 1024,
            ping_interval=None,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws is not None:
            await self.ws.close()

    async def evaluate(self, expression: str):
        assert self.ws is not None
        request_id = self.next_id
        self.next_id += 1
        await self.ws.send(
            json.dumps(
                {
                    "id": request_id,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression,
                        "returnByValue": True,
                        "awaitPromise": True,
                    },
                }
            )
        )
        while True:
            message = json.loads(await self.ws.recv())
            if message.get("id") != request_id:
                continue
            result = message["result"]["result"]
            if result.get("subtype") == "error":
                raise RuntimeError(result.get("description", result))
            return result.get("value")


def _js(instrument_ids: list[str], dates: list[str]) -> str:
    """Build one raw ProductQuery request inside the existing authenticated tab.

    Do not depend on CIQ's mutable front-end module registry.  The service
    accepts the same perspective/field contract directly and the browser adds
    the existing session cookies because ``credentials='include'`` is used.
    """

    return r'''(async()=>{
 const ids=__IDS__,dates=__DATES__;
 const fields=[
   {primary:322517,secondary:null,tertiary:null,originalSecondary:null,originalTertiary:null,context:null},
   {primary:322518,secondary:null,tertiary:null,originalSecondary:null,originalTertiary:null,context:null},
 ];
 for(const d of dates){
   fields.push({primary:322797,secondary:d,tertiary:'1D',originalSecondary:null,originalTertiary:null,context:null});
   fields.push({primary:324251,secondary:d,tertiary:null,originalSecondary:null,originalTertiary:null,context:null});
   fields.push({primary:324277,secondary:d,tertiary:null,originalSecondary:null,originalTertiary:null,context:null});
 }
 const req={
   conversionInformation:{keyCurrency:'USD',measurementStandard:1,conversionMode:0,magnitudeOverride:null,nullValue:'NA',dataLanguage:'en-GB',requestCulture:'en-US',reportingBasis:'Current/Restated',dateComparison:'Filing Date',industryClassification:'1',packageTrancheClassification:'0'},
   clientContext:{templatedId:null,clientVersion:'1.0',machineId:'00000000-0000-0000-0000-000000000000',disableLogging:false,is64Bit:false,keyClientCodes:null,isGrouped:false,randomClientCodes:null,excelCulture:'en-US',requestSource:5,forceLocalQueries:false,enableStatistics:false},
   functionRequests:[{perspective:321247,requestedPerspective:321247,operationType:2,keys:ids,fields,query:null,functionId:0,groomingStrategyApplied:false,groomedColumnOrdinal:null,groomedRowOrdinal:null,conversionInfo:null,requestedKeys:null,userDefinedFormulas:[],groupByField:null}]
 };
 const http=await fetch('/SNL.Services.Data.Service/v1/ProductQuery.svc/productQueryRequests',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(req)});
 const text=await http.text();
 if(!http.ok) throw new Error(`productquery_http_${http.status}:${text.slice(0,1000)}`);
 const resp=JSON.parse(text),out=(resp.functionResponses||[])[0]||{};
 return {responseException:out.responseException||null,headers:(out.headerInformation||[]).map((h,i)=>({i,caption:h.displayCaption,keyItem:String(h.keyItem),secondary:h.secondary,tertiary:h.tertiary,requestedColumn:h.requestedColumn})),rows:out.results||[],fields};
})()'''.replace("__IDS__", json.dumps(instrument_ids)).replace("__DATES__", json.dumps(dates))


def _master(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    required = [
        "SP_ENTITY_ID",
        "SP_SECURITY_ID",
        "SP_CIQ_ID",
        "SPT_INSTRUMENT_ITEM_ID",
        "SP_TRADING_ITEM_ID",
    ]
    if any(column not in frame.columns for column in required):
        raise ValueError("master_required_columns_missing")
    frame = frame.copy()
    for column in required:
        frame[column] = frame[column].astype(str).str.strip()
        if frame[column].eq("").any() or frame[column].duplicated().any():
            raise ValueError(f"master_identity_invalid:{column}")
    if not frame["SPT_INSTRUMENT_ITEM_ID"].eq("SPT" + frame["SP_TRADING_ITEM_ID"]).all():
        raise ValueError("master_spt_alias_mismatch")
    if not frame["SP_SECURITY_ID"].eq(frame["SP_CIQ_ID"]).all():
        raise ValueError("master_security_alias_mismatch")
    return frame.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)


def _write_part(
    *,
    out_path: Path,
    result: dict[str, object],
    master: pd.DataFrame,
    dates: list[str],
    retrieved_at: str,
) -> dict[str, object]:
    if result.get("responseException") is not None:
        raise ValueError(f"provider_response_exception:{result.get('responseException')}")
    rows = result.get("rows") or []
    headers = result.get("headers") or []
    if len(rows) != len(master):
        raise ValueError(f"provider_row_count_mismatch:{len(rows)}/{len(master)}")
    header_map: dict[tuple[str, str, str], int] = {}
    for header in headers:
        header_map[
            (
                str(header.get("caption") or ""),
                str(header.get("secondary") or ""),
                str(header.get("tertiary") or ""),
            )
        ] = int(header["i"])
    mi_idx = next(int(h["i"]) for h in headers if str(h.get("caption")) == "MI KEY")
    ciq_idx = next(int(h["i"]) for h in headers if str(h.get("caption")) == "SPCIQ ID")
    by_spt = master.set_index("SPT_INSTRUMENT_ITEM_ID", drop=False)
    observed: set[str] = set()
    output: list[dict[str, str]] = []
    for provider_row in rows:
        instrument = str(provider_row[1]).strip()
        if instrument not in by_spt.index:
            raise ValueError(f"provider_unrequested_instrument:{instrument}")
        if instrument in observed:
            raise ValueError(f"provider_duplicate_instrument:{instrument}")
        observed.add(instrument)
        source = by_spt.loc[instrument]
        returned_entity = str(provider_row[mi_idx]).strip()
        returned_ciq = str(provider_row[ciq_idx]).strip()
        if returned_entity != source["SP_ENTITY_ID"] or returned_ciq != source["SP_CIQ_ID"]:
            raise ValueError(f"provider_identity_mismatch:{instrument}")
        for date in dates:
            ret_idx = header_map[("Total Return", date, "1D")]
            close_idx = header_map[("Close Price", date, "")]
            volume_idx = header_map[("Trading Volume", date, "")]
            ret = _value(provider_row[ret_idx])
            close = _value(provider_row[close_idx])
            volume = _value(provider_row[volume_idx])
            output.append(
                {
                    "SPT_DATE": pd.Timestamp(date).date().isoformat(),
                    "SP_ENTITY_ID": source["SP_ENTITY_ID"],
                    "SP_SECURITY_ID": source["SP_SECURITY_ID"],
                    "SP_CIQ_ID": source["SP_CIQ_ID"],
                    "SPT_INSTRUMENT_ITEM_ID": source["SPT_INSTRUMENT_ITEM_ID"],
                    "SP_TRADING_ITEM_ID": source["SP_TRADING_ITEM_ID"],
                    "SPT_TOTAL_RETURN": ret,
                    "SP_TOTAL_RETURN": ret,
                    "SPT_CLOSE": close,
                    "SP_PRICE_CLOSE": close,
                    "SPT_VOLUME": volume,
                    "SP_VOLUME": volume,
                    "chunk_retrieved_at_utc": retrieved_at,
                    "RETURN_SOURCE_METRIC": "SPT_TOTAL_RETURN_1D_PERCENT",
                    "CLOSE_SOURCE_METRIC": "SPT_PRICE_CLOSE",
                    "VOLUME_SOURCE_METRIC": "SPT_VOLUME",
                }
            )
    if observed != set(master["SPT_INSTRUMENT_ITEM_ID"]):
        raise ValueError("provider_instrument_coverage_incomplete")
    output.sort(key=lambda row: (row["SPT_DATE"], int(row["SP_ENTITY_ID"])))
    _atomic_csv(out_path, output)
    complete = sum(
        row["SPT_TOTAL_RETURN"] != "NA"
        and row["SPT_CLOSE"] != "NA"
        and row["SPT_VOLUME"] != "NA"
        for row in output
    )
    return {
        "rows": len(output),
        "complete_cells_triplets": complete,
        "sha256": _sha256(out_path),
        "bytes": out_path.stat().st_size,
    }


def _receipt_payload(
    *,
    out_path: Path,
    master_path: Path,
    master: pd.DataFrame,
    chunk: pd.DatetimeIndex,
    retrieved_at: str,
    stats: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": PART_SCHEMA,
        "source_id": SOURCE_ID,
        "provider": EXPECTED_PROVIDER,
        "captured_at_utc": retrieved_at,
        "market_perspective": MARKET_PERSPECTIVE,
        "query_identity_field_key": QUERY_IDENTITY_FIELD,
        "query_identity_alias": "SPT_INSTRUMENT_ITEM_ID",
        "mi_key_field_key": MI_KEY_FIELD,
        "ciq_id_field_key": CIQ_ID_FIELD,
        "total_return_field_key": TOTAL_RETURN_FIELD,
        "total_return_alias": "SPT_TOTAL_RETURN",
        "total_return_period_secondary_key": TOTAL_RETURN_PERIOD_SECONDARY_KEY,
        "total_return_period": TOTAL_RETURN_PERIOD,
        "price_field_key": PRICE_FIELD,
        "price_alias": "SPT_PRICE_CLOSE",
        "volume_field_key": VOLUME_FIELD,
        "volume_alias": "SPT_VOLUME",
        "date_secondary_key": DATE_SECONDARY_KEY,
        "start_date": pd.Timestamp(chunk[0]).date().isoformat(),
        "end_date": pd.Timestamp(chunk[-1]).date().isoformat(),
        "weekday_count": len(chunk),
        "entity_count": len(master),
        "raw_grid_rows": stats["rows"],
        "complete_triplets": stats["complete_cells_triplets"],
        "raw_object_name": out_path.name,
        "raw_object_sha256": stats["sha256"],
        "raw_object_bytes": stats["bytes"],
        "master_name": master_path.name,
        "master_sha256": _sha256(master_path),
        "current_primary_conditioned": False,
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }


def _load_resumable_part(
    *,
    out_path: Path,
    receipt_path: Path,
    master_path: Path,
    master: pd.DataFrame,
    chunk: pd.DatetimeIndex,
) -> dict[str, object] | None:
    csv_exists = out_path.is_file()
    receipt_exists = receipt_path.is_file()
    if not csv_exists and not receipt_exists:
        return None
    if csv_exists != receipt_exists:
        raise ValueError(f"resume_partial_part_present:{out_path.name}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    expected = {
        "schema_version": PART_SCHEMA,
        "source_id": SOURCE_ID,
        "provider": EXPECTED_PROVIDER,
        "market_perspective": MARKET_PERSPECTIVE,
        "query_identity_field_key": QUERY_IDENTITY_FIELD,
        "total_return_field_key": TOTAL_RETURN_FIELD,
        "price_field_key": PRICE_FIELD,
        "volume_field_key": VOLUME_FIELD,
        "date_secondary_key": DATE_SECONDARY_KEY,
        "start_date": pd.Timestamp(chunk[0]).date().isoformat(),
        "end_date": pd.Timestamp(chunk[-1]).date().isoformat(),
        "weekday_count": len(chunk),
        "entity_count": len(master),
        "master_sha256": _sha256(master_path),
        "current_primary_conditioned": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"resume_receipt_mismatch:{out_path.name}:{key}")
    if receipt.get("raw_object_name") != out_path.name:
        raise ValueError(f"resume_receipt_object_name_mismatch:{out_path.name}")
    if receipt.get("raw_object_sha256") != _sha256(out_path):
        raise ValueError(f"resume_raw_hash_mismatch:{out_path.name}")
    if int(receipt.get("raw_object_bytes", -1)) != out_path.stat().st_size:
        raise ValueError(f"resume_raw_bytes_mismatch:{out_path.name}")
    frame = pd.read_csv(out_path, dtype=str)
    if len(frame) != len(master) * len(chunk):
        raise ValueError(f"resume_raw_grid_rows_mismatch:{out_path.name}")
    if int(receipt.get("raw_grid_rows", -1)) != len(frame):
        raise ValueError(f"resume_receipt_grid_rows_mismatch:{out_path.name}")
    return receipt


def _part_manifest_entry(out_path: Path, receipt_path: Path, receipt: dict[str, Any]) -> dict[str, object]:
    return {
        "csv": out_path.name,
        "csv_sha256": _sha256(out_path),
        "receipt": receipt_path.name,
        "receipt_sha256": _sha256(receipt_path),
        "start_date": receipt["start_date"],
        "end_date": receipt["end_date"],
        "rows": int(receipt["raw_grid_rows"]),
        "complete_triplets": int(receipt["complete_triplets"]),
    }


async def main_async(args: argparse.Namespace) -> None:
    master_path = Path(args.master)
    master = _master(master_path)
    if len(master) != args.expected_entities:
        raise ValueError(f"master_entity_count_mismatch:{len(master)}/{args.expected_entities}")
    dates = pd.bdate_range(args.start, args.end)
    if len(dates) == 0:
        raise ValueError("weekday_grid_empty")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    instrument_ids = master["SPT_INSTRUMENT_ITEM_ID"].tolist()
    manifest_parts: list[dict[str, object]] = []
    chunks = [dates[offset : offset + args.chunk_dates] for offset in range(0, len(dates), args.chunk_dates)]

    async with Cdp(args.port) as cdp:
        for chunk_index, chunk in enumerate(chunks):
            start_stamp = pd.Timestamp(chunk[0]).strftime("%Y%m%d")
            end_stamp = pd.Timestamp(chunk[-1]).strftime("%Y%m%d")
            out_path = out_dir / f"part_{chunk_index:03d}_{start_stamp}_{end_stamp}.csv"
            receipt_path = out_dir / f"part_{chunk_index:03d}_{start_stamp}_{end_stamp}.receipt.json"
            existing = _load_resumable_part(
                out_path=out_path,
                receipt_path=receipt_path,
                master_path=master_path,
                master=master,
                chunk=chunk,
            )
            if existing is not None:
                if not args.resume:
                    raise FileExistsError(f"capture_output_exists:{out_path}")
                manifest_parts.append(_part_manifest_entry(out_path, receipt_path, existing))
                print(
                    "MARKET_PART_REUSED"
                    f"\tINDEX={chunk_index}\tDATES={len(chunk)}\tROWS={existing['raw_grid_rows']}"
                    f"\tCOMPLETE={existing['complete_triplets']}\tSHA256={existing['raw_object_sha256']}"
                )
                continue

            date_values = [pd.Timestamp(date).strftime("%m/%d/%Y") for date in chunk]
            result = await cdp.evaluate(_js(instrument_ids, date_values))
            retrieved_at = datetime.now(UTC).isoformat()
            stats = _write_part(
                out_path=out_path,
                result=result,
                master=master,
                dates=date_values,
                retrieved_at=retrieved_at,
            )
            receipt = _receipt_payload(
                out_path=out_path,
                master_path=master_path,
                master=master,
                chunk=chunk,
                retrieved_at=retrieved_at,
                stats=stats,
            )
            _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            manifest_parts.append(_part_manifest_entry(out_path, receipt_path, receipt))
            print(
                "MARKET_PART_OK"
                f"\tINDEX={chunk_index}\tDATES={len(chunk)}\tROWS={stats['rows']}"
                f"\tCOMPLETE={stats['complete_cells_triplets']}\tSHA256={stats['sha256']}"
            )

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "source_id": SOURCE_ID,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "start_date": pd.Timestamp(dates[0]).date().isoformat(),
        "end_date": pd.Timestamp(dates[-1]).date().isoformat(),
        "weekday_count": len(dates),
        "entity_count": len(master),
        "part_count": len(manifest_parts),
        "chunk_dates": args.chunk_dates,
        "master_name": master_path.name,
        "master_sha256": _sha256(master_path),
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "parts": manifest_parts,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    manifest_path = out_dir / "market_capture.manifest.json"
    if manifest_path.exists() and not args.resume:
        raise FileExistsError(f"capture_manifest_exists:{manifest_path}")
    _atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"MARKET_CAPTURE_OK\tPARTS={len(manifest_parts)}\tWEEKDAYS={len(dates)}"
        f"\tENTITIES={len(master)}\tMANIFEST_SHA256={_sha256(manifest_path)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--master", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--chunk-dates", type=int, default=20)
    parser.add_argument("--expected-entities", type=int, default=104)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.chunk_dates < 1 or args.chunk_dates > 20:
        raise ValueError("chunk_dates_out_of_range:1..20")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
