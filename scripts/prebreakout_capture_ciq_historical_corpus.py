"""Capture the real PREBREAKOUT historical market/listing corpus via existing CIQ Pro session.

This is an acquisition entrypoint, not a PIT abstraction. It reuses the already-proved
Capital IQ Pro Advanced Search / Securities ProductQuery contract:

* perspective 321247;
* exact-date Close Price NotNa predicate (field 324251, sk_557 semantics);
* Major US Exchanges group field 406718 = -1,-4;
* funding/equity field 321268 in {1,16};
* exact security identity from SP_CIQ_ID and exact SPT Trading Item identity;
* same-date Close / 1D Total Return / Volume.

The script never signs in, signs out, launches, or navigates Capital IQ Pro. It attaches
to an already-running Chromium DevTools target and uses the existing authenticated page.
Each date is an atomic, resumable part. No current-primary field is requested. Date-local
primary proof is derived only from exact uniqueness among the source-qualified listings
for a company on that date; multiple qualifying listings are retained as ambiguous.

This script does not open outcomes, run Trial-1, or create capital authority.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import UTC, date, datetime, time
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import websockets


SCHEMA = "prebreakout_ciq_historical_corpus_capture_v1"
PART_RECEIPT_SCHEMA = "prebreakout_ciq_date_local_market_part_receipt_v1"
MANIFEST_SCHEMA = "prebreakout_ciq_historical_corpus_manifest_v1"
FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
RISK_SET_SPEC_ID = "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
W2_CONTRACT_SHA256 = "94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71"
PERSPECTIVE = "321247"
EXCHANGE_GROUP_FIELD = "406718"
EXCHANGE_GROUP_VALUE = "-1,-4"
FUNDING_TYPE_FIELD = "321268"
FUNDING_TYPE_VALUES = ("1", "16")
PRICE_FIELD = "324251"
TOTAL_RETURN_FIELD = "322797"
VOLUME_FIELD = "324277"
DATE_SECONDARY_KEY = "sk_557"
TOTAL_RETURN_PERIOD = "1D"
PROVIDER = "S&P Capital IQ Pro authenticated existing web session"
LICENSE_SCOPE = "SPCIQPRO_LOCAL_RESEARCH_ENTITLEMENT"
RETENTION_CLASS = "LOCAL_RESEARCH_CUSTODY"
NY_TZ = ZoneInfo("America/New_York")
REGULAR_CLOSE = time(16, 0)

# Identity/detail fields proven in the retained Lane-2 query. Primary Issue 324610
# is intentionally absent because it is current-conditioned.
EXTRA_FIELDS = ("322517", "390627", "322518", "326421", "326424", "324426", "321281", "322197")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("prebreakout_ciq_capture_rows_required")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.upper() in {"NA", "N/A", "NAN", "NULL", "NONE", "KEYERROR"}:
        return ""
    return text


def _session_close_utc(day: date) -> datetime:
    # The screen predicate itself proves a traded date. The historical acquisition
    # contract intentionally uses the regular 16:00 NY close as the conservative
    # information boundary; any future early-close support must carry its own
    # date-specific calendar authority before prospective use.
    return datetime.combine(day, REGULAR_CLOSE, tzinfo=NY_TZ).astimezone(UTC)


class Cdp:
    def __init__(self, port: int):
        self.port = int(port)
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
        # Do not send a synthetic Origin. Modern Chromium rejects it unless the
        # debugger was launched with an explicit origin allow-list.
        self.ws = await websockets.connect(
            page["webSocketDebuggerUrl"],
            max_size=256 * 1024 * 1024,
            ping_interval=None,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws is not None:
            await self.ws.close()

    async def evaluate(self, expression: str) -> Any:
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
            envelope = message.get("result", {})
            if envelope.get("exceptionDetails") is not None:
                details = envelope["exceptionDetails"]
                raise RuntimeError(str(details.get("text") or details))
            result = envelope.get("result", {})
            if result.get("subtype") == "error":
                raise RuntimeError(result.get("description", result))
            return result.get("value")


def _screen_js(date_text: str) -> str:
    """Build the proven Securities screening request without front-end modules."""

    display_date = pd.Timestamp(date_text).strftime("%Y/%m/%d")
    provider_date = pd.Timestamp(date_text).strftime("%m/%d/%Y")
    return r"""(async()=>{
 const date=__DATE__, displayDate=__DISPLAY_DATE__;
 const field=(primary,secondary=null,tertiary=null)=>({primary:Number(primary),exportPrimary:Number(primary),secondary,tertiary,contextJson:null,originalSecondary:null,originalTertiary:null,context:null});
 const fields=__EXTRA_FIELDS__.map(x=>field(x));
 fields.push(field('324251',date,null));
 fields.push(field('322797',date,'1D'));
 fields.push(field('324277',date,null));
 const line=(fieldKey,operator,value,secondaryKeys=null)=>({rankingMappingGUID:null,rankingSubVQAlias:null,beginGroup:false,connector:0,displayText:null,endGroup:false,field:{displayName:null,displayType:null,displayUnits:null,exportFieldKey:null,fieldKey:String(fieldKey),foreignPerspective:null,originalRequestField:null,secondaryKeys},functionName:null,invariantValue:null,isRankScreeningQueryLine:false,listKey:null,mathOperator:0,mathValue:null,operator,queryItemId:'00000000-0000-0000-0000-000000000000',relativeOperation:false,sortOrder:null,sortStyle:null,supressSelect:false,value:String(value),valueField:null});
 const queryLines=[
   line('406718',7,"'-1,-4'"),
   line('321268',7,"'1','16'"),
   line('324251',22,'',[{displayValue:displayDate,keyJointHint:'sk_557',value:date}])
 ];
 const req={
   conversionInformation:{keyCurrency:'USD',measurementStandard:1,conversionMode:0,magnitudeOverride:null,nullValue:'NA',dataLanguage:'en-GB',requestCulture:'en-US',reportingBasis:'Current/Restated',dateComparison:'Filing Date',industryClassification:'1',packageTrancheClassification:'0'},
   clientContext:{templatedId:null,clientVersion:'1.0',machineId:'00000000-0000-0000-0000-000000000000',disableLogging:false,is64Bit:false,keyClientCodes:null,isGrouped:false,randomClientCodes:null,excelCulture:'en-US',requestSource:5,forceLocalQueries:false,enableStatistics:false},
   functionRequests:[{
     perspective:321247,requestedPerspective:321247,operationType:22,
     fields,reports:[{name:'Custom Screener Report 1',fields,reportType:'report'}],groupByField:null,keys:null,pagingInfo:null,sortByFieldsOrdered:null,
     query:{keyPerspective:'321247',baseCompany:null,queryFilters:[],queryLineGroups:[{groupName:'QueryLines',queryLines},{groupName:'WhiteAndBlackListCriteria',queryLines:[]},{groupName:'RankingCriteria',queryLines:[]}]},
     functionId:0,groomingStrategyApplied:false,groomedColumnOrdinal:null,groomedRowOrdinal:null,conversionInfo:null,requestedKeys:null,userDefinedFormulas:[]
   }],
   userDefinedFormulas:[],userDefinedCriteria:[],
   extensionPropertiesJson:JSON.stringify({userDefinedFormulas:[],hideQueryFilter:false,queryLineToFieldMappings:{queryLineToFieldMappings:[]},maximumRowLimit:250000,maximumColumnLimit:200,maximumCellLimit:10000000,forceLocalQueries:false})
 };
 const http=await fetch('/SNL.Services.Data.Service/v1/ProductQuery.svc/productQueryRequests',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(req)});
 const text=await http.text();
 if(!http.ok) throw new Error(`productquery_http_${http.status}:${text.slice(0,1000)}`);
 const resp=JSON.parse(text),out=(resp.functionResponses||[])[0]||{};
 return {responseException:out.responseException||null,headers:(out.headerInformation||[]).map((h,i)=>({i,displayCaption:String(h.displayCaption||''),keyItem:String(h.keyItem||''),secondary:h.secondary==null?'':String(h.secondary),tertiary:h.tertiary==null?'':String(h.tertiary),requestedColumn:h.requestedColumn})),rows:out.results||[],requestFieldPrimaries:fields.map(x=>String(x.primary)),queryLines};
})()""".replace("__DATE__", json.dumps(provider_date)).replace("__DISPLAY_DATE__", json.dumps(display_date)).replace("__EXTRA_FIELDS__", json.dumps(list(EXTRA_FIELDS)))


def _header_index(headers: list[dict[str, Any]], *, caption: str | None = None, key_item: str | None = None, secondary: str | None = None, tertiary: str | None = None) -> int:
    matches = []
    for header in headers:
        if caption is not None and str(header.get("displayCaption")) != caption:
            continue
        if key_item is not None and str(header.get("keyItem")) != key_item:
            continue
        if secondary is not None and str(header.get("secondary") or "") != secondary:
            continue
        if tertiary is not None and str(header.get("tertiary") or "") != tertiary:
            continue
        matches.append(int(header["i"]))
    if len(matches) != 1:
        raise ValueError(f"prebreakout_header_not_exact:{caption}:{key_item}:{secondary}:{tertiary}:{matches}")
    return matches[0]


def _normalize_date_result(*, result: dict[str, Any], session_date: str, retrieved_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if result.get("responseException") is not None:
        raise ValueError(f"prebreakout_provider_response_exception:{result.get('responseException')}")
    rows = result.get("rows")
    headers = result.get("headers")
    if not isinstance(rows, list) or not isinstance(headers, list):
        raise ValueError("prebreakout_provider_result_shape_invalid")
    if not rows:
        return [], {"source_security_row_count": 0, "source_entity_count": 0, "ambiguous_entity_count": 0}

    # Stable captions / key-items proven in Lane-2.
    mi_idx = _header_index(headers, caption="MI KEY")
    ciq_idx = _header_index(headers, caption="SPCIQ ID")
    ticker_idx = next((int(h["i"]) for h in headers if str(h.get("keyItem")) == "907"), None)
    exchange_idx = next((int(h["i"]) for h in headers if str(h.get("keyItem")) == "1154"), None)
    equity_type_idx = next((int(h["i"]) for h in headers if str(h.get("keyItem")) == "1054"), None)
    date_value = pd.Timestamp(session_date).strftime("%m/%d/%Y")
    close_idx = _header_index(headers, caption="Close Price", secondary=date_value, tertiary="")
    ret_idx = _header_index(headers, caption="Total Return", secondary=date_value, tertiary="1D")
    volume_idx = _header_index(headers, caption="Trading Volume", secondary=date_value, tertiary="")

    close_available_at = _session_close_utc(pd.Timestamp(session_date).date()).isoformat(timespec="microseconds").replace("+00:00", "Z")
    staged: list[dict[str, Any]] = []
    for provider_row in rows:
        if not isinstance(provider_row, list):
            raise ValueError("prebreakout_provider_row_not_list")
        spt = _value(provider_row[1])
        if not spt.startswith("SPT") or not spt[3:].isdigit():
            raise ValueError(f"prebreakout_provider_spt_invalid:{spt}")
        entity = _value(provider_row[mi_idx])
        ciq = _value(provider_row[ciq_idx])
        if not entity.isdigit() or not ciq.startswith("IQ") or not ciq[2:].isdigit():
            raise ValueError(f"prebreakout_provider_identity_invalid:{entity}:{ciq}:{spt}")
        close = _value(provider_row[close_idx])
        total_return = _value(provider_row[ret_idx])
        volume = _value(provider_row[volume_idx])
        market_complete = bool(close and total_return and volume)
        staged.append(
            {
                "SP_ENTITY_ID": entity,
                "SP_CIQ_ID": ciq,
                "SP_TRADING_ITEM_ID": spt[3:],
                "SPT_INSTRUMENT_ITEM_ID": spt,
                "TICKER": _value(provider_row[ticker_idx]) if ticker_idx is not None else "",
                "EXCHANGE": _value(provider_row[exchange_idx]) if exchange_idx is not None else "",
                "PROVIDER_EQUITY_TYPE": _value(provider_row[equity_type_idx]) if equity_type_idx is not None else "",
                "LISTING_COUNTRY": "US",
                "SECURITY_CLASS": "COMMON_EQUITY",
                "TRADING_STATUS": "ACTIVE_TRADABLE" if close else "MARKET_OBSERVATION_UNRESOLVED",
                "MEMBERSHIP_AS_OF_DATE": session_date,
                "SP_PRICE_CLOSE": close,
                "SP_TOTAL_RETURN": total_return,
                "SP_VOLUME": volume,
                "OBSERVED_AT": close_available_at,
                "AVAILABLE_AT": close_available_at,
                "RETRIEVED_AT": retrieved_at,
            }
        )

    if len({(r["SP_CIQ_ID"], r["SP_TRADING_ITEM_ID"]) for r in staged}) != len(staged):
        raise ValueError("prebreakout_date_local_identity_duplicate")
    by_entity: dict[str, list[dict[str, Any]]] = {}
    for row in staged:
        by_entity.setdefault(str(row["SP_ENTITY_ID"]), []).append(row)
    for entity_rows in by_entity.values():
        if len(entity_rows) == 1:
            row = entity_rows[0]
            row["PRIMARY_LISTING_ID"] = row["SPT_INSTRUMENT_ITEM_ID"]
            row["PRIMARY_LISTING_STATE"] = "PRIMARY_DATE_LOCAL"
            row["PRIMARY_LISTING_PROOF_KIND"] = "UNIQUE_DATE_LOCAL_QUALIFYING_LISTING"
        else:
            for row in entity_rows:
                row["PRIMARY_LISTING_ID"] = ""
                row["PRIMARY_LISTING_STATE"] = "AMBIGUOUS_DATE_LOCAL"
                row["PRIMARY_LISTING_PROOF_KIND"] = "DATE_LOCAL_AMBIGUOUS_MULTIPLE"
    staged.sort(key=lambda r: (int(r["SP_ENTITY_ID"]), r["SPT_INSTRUMENT_ITEM_ID"]))
    return staged, {
        "source_security_row_count": len(staged),
        "source_entity_count": len(by_entity),
        "ambiguous_entity_count": sum(1 for values in by_entity.values() if len(values) != 1),
        "missing_close_count": sum(1 for row in staged if not row["SP_PRICE_CLOSE"]),
        "missing_total_return_count": sum(1 for row in staged if not row["SP_TOTAL_RETURN"]),
        "missing_volume_count": sum(1 for row in staged if not row["SP_VOLUME"]),
    }


def _part_paths(out_dir: Path, session_date: str) -> tuple[Path, Path]:
    stamp = session_date.replace("-", "")
    return (
        out_dir / f"date_{stamp}.csv",
        out_dir / f"date_{stamp}.receipt.json",
    )


def _verify_existing_part(csv_path: Path, receipt_path: Path, *, session_date: str) -> dict[str, Any]:
    if csv_path.is_file() != receipt_path.is_file():
        raise ValueError(f"prebreakout_resume_partial_part:{session_date}")
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    required = {
        "schema_version": PART_RECEIPT_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "session_date": session_date,
        "current_primary_conditioned": False,
        "current_survivor_conditioned": False,
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise ValueError(f"prebreakout_resume_receipt_mismatch:{session_date}:{key}")
    if receipt.get("raw_object_sha256") != _sha256(csv_path):
        raise ValueError(f"prebreakout_resume_hash_mismatch:{session_date}")
    if int(receipt.get("raw_object_bytes", -1)) != csv_path.stat().st_size:
        raise ValueError(f"prebreakout_resume_size_mismatch:{session_date}")
    frame = pd.read_csv(csv_path, dtype=str).fillna("")
    if len(frame) != int(receipt.get("source_security_row_count", -1)):
        raise ValueError(f"prebreakout_resume_row_count_mismatch:{session_date}")
    return receipt


async def capture_dates(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requested = [stamp.date().isoformat() for stamp in pd.bdate_range(args.start, args.end)]
    if args.max_dates is not None:
        requested = requested[: int(args.max_dates)]
    if not requested:
        raise ValueError("prebreakout_capture_date_range_empty")

    entries: list[dict[str, Any]] = []
    async with Cdp(args.port) as cdp:
        for index, session_date in enumerate(requested):
            csv_path, receipt_path = _part_paths(out_dir, session_date)
            if csv_path.exists() or receipt_path.exists():
                if not args.resume:
                    raise FileExistsError(f"prebreakout_capture_part_exists:{session_date}")
                receipt = _verify_existing_part(csv_path, receipt_path, session_date=session_date)
                entries.append(
                    {
                        "session_date": session_date,
                        "status": "REUSED",
                        "row_count": int(receipt["source_security_row_count"]),
                        "csv": csv_path.name,
                        "csv_sha256": _sha256(csv_path),
                        "receipt": receipt_path.name,
                        "receipt_sha256": _sha256(receipt_path),
                    }
                )
                print(f"PREBREAKOUT_DATE_REUSED\tINDEX={index}\tDATE={session_date}\tROWS={receipt['source_security_row_count']}", flush=True)
                continue

            result = await cdp.evaluate(_screen_js(session_date))
            retrieved_at = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
            rows, stats = _normalize_date_result(
                result=result,
                session_date=session_date,
                retrieved_at=retrieved_at,
            )
            if not rows:
                # Exact-date close NotNa returning zero rows is treated as a non-session.
                entries.append({"session_date": session_date, "status": "NO_MARKET_SESSION", "row_count": 0})
                print(f"PREBREAKOUT_DATE_NONSESSION\tINDEX={index}\tDATE={session_date}", flush=True)
                continue
            _atomic_csv(csv_path, rows)
            receipt = {
                "schema_version": PART_RECEIPT_SCHEMA,
                "capture_schema": SCHEMA,
                "family_id": FAMILY_ID,
                "risk_set_spec_id": RISK_SET_SPEC_ID,
                "w2_contract_sha256": W2_CONTRACT_SHA256,
                "source_id": "SPCIQPRO:SECURITIES_PRODUCTQUERY",
                "provider": PROVIDER,
                "market_perspective": PERSPECTIVE,
                "session_date": session_date,
                "provider_effective_as_of_date": session_date,
                "historical_as_of_mechanically_bound": True,
                "date_local_membership_query": True,
                "source_population_complete": True,
                "exchange_group_field_key": EXCHANGE_GROUP_FIELD,
                "exchange_group_value": EXCHANGE_GROUP_VALUE,
                "funding_type_field_key": FUNDING_TYPE_FIELD,
                "funding_type_values": list(FUNDING_TYPE_VALUES),
                "price_field_key": PRICE_FIELD,
                "total_return_field_key": TOTAL_RETURN_FIELD,
                "volume_field_key": VOLUME_FIELD,
                "price_date_secondary_key": DATE_SECONDARY_KEY,
                "total_return_period": TOTAL_RETURN_PERIOD,
                "primary_issue_field_requested": False,
                "current_primary_conditioned": False,
                "current_survivor_conditioned": False,
                "alternate_listing_backfill_used": False,
                "ticker_identity_fallback_used": False,
                "company_entity_risky_identity_fallback_used": False,
                "permno_fallback_used": False,
                "primary_listing_resolution": "UNIQUE_DATE_LOCAL_QUALIFYING_LISTING_OR_AMBIGUOUS_EXCLUDE",
                "retrieved_at": retrieved_at,
                "observed_range_start": session_date,
                "observed_range_end": session_date,
                "source_security_row_count": stats["source_security_row_count"],
                "source_entity_count": stats["source_entity_count"],
                "ambiguous_entity_count": stats["ambiguous_entity_count"],
                "missing_close_count": stats["missing_close_count"],
                "missing_total_return_count": stats["missing_total_return_count"],
                "missing_volume_count": stats["missing_volume_count"],
                "missing_market_policy": "RETAIN_ROW_NO_IMPUTATION_NO_ALTERNATE_LISTING_RESCUE",
                "raw_object_name": csv_path.name,
                "raw_object_sha256": _sha256(csv_path),
                "raw_object_bytes": csv_path.stat().st_size,
                "request_field_primaries": result.get("requestFieldPrimaries"),
                "query_lines": result.get("queryLines"),
                "license_scope": LICENSE_SCOPE,
                "retention_class": RETENTION_CLASS,
                "existing_session_reused": True,
                "sign_in_performed": False,
                "sign_out_performed": False,
                "outcome_access_performed": False,
                "financial_alpha_evidence": 0,
                "capital_authority": "NONE",
            }
            _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            entries.append(
                {
                    "session_date": session_date,
                    "status": "CAPTURED",
                    "row_count": len(rows),
                    "csv": csv_path.name,
                    "csv_sha256": _sha256(csv_path),
                    "receipt": receipt_path.name,
                    "receipt_sha256": _sha256(receipt_path),
                }
            )
            print(
                f"PREBREAKOUT_DATE_OK\tINDEX={index}\tDATE={session_date}\tROWS={len(rows)}"
                f"\tENTITIES={stats['source_entity_count']}\tAMBIG={stats['ambiguous_entity_count']}"
                f"\tSHA256={_sha256(csv_path)}",
                flush=True,
            )

    sessions = [entry for entry in entries if entry["status"] in {"CAPTURED", "REUSED"}]
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "capture_schema": SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "requested_start_date": requested[0],
        "requested_end_date": requested[-1],
        "requested_business_date_count": len(requested),
        "market_session_count": len(sessions),
        "non_session_count": len(entries) - len(sessions),
        "provider": PROVIDER,
        "provider_capture_performed": any(entry["status"] == "CAPTURED" for entry in entries),
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "parts": entries,
        "license_scope": LICENSE_SCOPE,
        "retention_class": RETENTION_CLASS,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    manifest_path = out_dir / "capture.manifest.json"
    _atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"PREBREAKOUT_CAPTURE_OK\tSESSIONS={len(sessions)}\tREQUESTED={len(requested)}"
        f"\tMANIFEST_SHA256={_sha256(manifest_path)}\tPATH={manifest_path}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-dates", type=int)
    args = parser.parse_args()
    if args.max_dates is not None and args.max_dates < 1:
        raise ValueError("prebreakout_max_dates_must_be_positive")
    asyncio.run(capture_dates(args))


if __name__ == "__main__":
    main()
