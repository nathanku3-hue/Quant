"""Capture source-bound CIQ Key Developments for the PREBREAKOUT corpus union.

Operational acquisition only. The script attaches to the existing authenticated
Capital IQ Pro Chromium session and queries perspective 311682 for explicit company
batches. It never signs in/out or navigates. Raw event rows are retained with exact
company mappings so a later deterministic compiler can derive per-date lifecycle
state without consulting current Company/Security status.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

import requests
import websockets


FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
W2_CONTRACT_SHA256 = "94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71"
PERSPECTIVE = "311682"
ENTITY_FILTER_FIELD = "398876"
EVENT_DATE_FIELD = "311764"
ROLE_SECONDARY_KEY = "sk_50017"
ROLE_SECONDARY_VALUE = "1"
EVENT_TYPE_FIELD = "322182"
EVENT_TYPE_SECONDARY_KEY = "sk_50016"
# Frozen W3 lifecycle-relevant provider categories only. These are source-side
# query criteria, not a post-capture survivor filter.
LIFECYCLE_EVENT_TYPE_KEYS = (
    "9496", "9497", "9498",          # bankruptcy conclusion/emergence/filing
    "9508", "9509", "9510",          # M&A announcement/cancellation/closing
    "9515", "9516", "9517", "9518", "9519", "9520", "9521", "9522",
    "9559",                             # split / significant stock dividend audit
    "9607", "9609", "9613",          # delisting / exchange / ticker change
    "9621", "9629",                    # distress/listing delisting variants
    "9657", "9658", "9659", "9660", "9661", "9662", "9663",
)
EXTRA_FIELDS = (EVENT_TYPE_FIELD, "311765", "311766", "311769")
PART_SCHEMA = "prebreakout_ciq_key_developments_part_receipt_v1"
MANIFEST_SCHEMA = "prebreakout_ciq_key_developments_manifest_v1"
PROVIDER = "S&P Capital IQ Pro authenticated existing web session"
LICENSE_SCOPE = "SPCIQPRO_LOCAL_RESEARCH_ENTITLEMENT"
RETENTION_CLASS = "LOCAL_RESEARCH_CUSTODY"


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


def _atomic_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["SP_ENTITY_ID", "EVENT_DATE", "EVENT_OID", "EVENT_TYPE", "HEADLINE", "DESCRIPTION"]
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


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
        self.ws = await websockets.connect(
            page["webSocketDebuggerUrl"], max_size=512 * 1024 * 1024, ping_interval=None
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
                raise RuntimeError(str(envelope["exceptionDetails"].get("text") or envelope["exceptionDetails"]))
            result = envelope.get("result", {})
            if result.get("subtype") == "error":
                raise RuntimeError(result.get("description", result))
            return result.get("value")


def _query_js(entity_ids: list[str]) -> str:
    return r"""(async()=>{
 const ids=__IDS__;
 const field=primary=>({primary:Number(primary),exportPrimary:Number(primary),secondary:null,tertiary:null,contextJson:null,originalSecondary:null,originalTertiary:null,context:null});
 const fields=__FIELDS__.map(field);
 const addCompaniesValue=JSON.stringify({companyKeys:ids,fundKeys:[],fixedIncomeKeys:[],equitiesKeys:[],listKeys:[],portfolioKeys:[]});
 const queryLine={rankingMappingGUID:null,rankingSubVQAlias:null,beginGroup:false,connector:0,displayText:'',endGroup:false,field:{displayName:null,displayType:null,displayUnits:null,exportFieldKey:'',fieldKey:'398876',foreignPerspective:null,originalRequestField:null,secondaryKeys:[{displayValue:'',key:'1',keyJointHint:'sk_50017',mask:'1',value:'1',keyOption:0}]},functionName:null,invariantValue:null,isRankScreeningQueryLine:false,listKey:null,mathOperator:0,mathValue:null,operator:7,queryItemId:'00000000-0000-0000-0000-000000000000',relativeOperation:false,sortOrder:null,sortStyle:null,supressSelect:false,value:addCompaniesValue,valueField:null};
 const typeLine={rankingMappingGUID:null,rankingSubVQAlias:null,beginGroup:false,connector:0,displayText:'',endGroup:false,field:{displayName:null,displayType:null,displayUnits:null,exportFieldKey:'',fieldKey:'322182',foreignPerspective:null,originalRequestField:null,secondaryKeys:null},functionName:null,invariantValue:null,isRankScreeningQueryLine:false,listKey:null,mathOperator:0,mathValue:null,operator:7,queryItemId:'00000000-0000-0000-0000-000000000000',relativeOperation:false,sortOrder:null,sortStyle:null,supressSelect:false,value:__EVENT_VALUES__,valueField:null};
 const req={
   conversionInformation:{keyCurrency:'USD',measurementStandard:1,conversionMode:0,magnitudeOverride:null,nullValue:'NA',dataLanguage:'en-GB',requestCulture:'en-US',reportingBasis:'Current/Restated',dateComparison:'Filing Date',industryClassification:'1',packageTrancheClassification:'0'},
   clientContext:{templatedId:null,clientVersion:'1.0',machineId:'00000000-0000-0000-0000-000000000000',disableLogging:false,is64Bit:false,keyClientCodes:null,isGrouped:false,randomClientCodes:null,excelCulture:'en-US',requestSource:5,forceLocalQueries:false,enableStatistics:false},
   functionRequests:[{
     perspective:311682,requestedPerspective:311682,operationType:22,
     fields,reports:[{name:'Custom Screener Report 1',fields,reportType:'report'}],groupByField:null,keys:null,pagingInfo:null,sortByFieldsOrdered:null,
     query:{keyPerspective:'311682',baseCompany:null,queryFilters:[],queryLineGroups:[{groupName:'QueryLines',queryLines:[queryLine,typeLine]},{groupName:'WhiteAndBlackListCriteria',queryLines:[]},{groupName:'RankingCriteria',queryLines:[]}]},
     functionId:0,groomingStrategyApplied:false,groomedColumnOrdinal:null,groomedRowOrdinal:null,conversionInfo:null,requestedKeys:null,userDefinedFormulas:[]
   }],
   userDefinedFormulas:[],userDefinedCriteria:[],
   extensionPropertiesJson:JSON.stringify({userDefinedFormulas:[],queryLineToFieldMappings:{queryLineToFieldMappings:[]},maximumRowLimit:250000,maximumColumnLimit:200,maximumCellLimit:10000000,forceLocalQueries:false,dotNetFrameworkVersion:null,hideQueryFilter:true})
 };
 const http=await fetch('/SNL.Services.Data.Service/v1/ProductQuery.svc/productQueryRequests',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(req)});
 const text=await http.text(); if(!http.ok) throw new Error(`productquery_http_${http.status}:${text.slice(0,1000)}`);
 const resp=JSON.parse(text),out=(resp.functionResponses||[])[0]||{};
 return {responseException:out.responseException||null,headers:(out.headerInformation||[]).map((h,i)=>({i,caption:String(h.displayCaption||''),keyItem:String(h.keyItem||''),secondary:h.secondary==null?'':String(h.secondary),tertiary:h.tertiary==null?'':String(h.tertiary)})),rows:out.results||[],requestedEntityIds:ids};
})()""".replace("__IDS__", json.dumps(entity_ids)).replace("__FIELDS__", json.dumps(list(EXTRA_FIELDS))).replace("__EVENT_VALUES__", json.dumps(",".join("'" + value + "'" for value in LIFECYCLE_EVENT_TYPE_KEYS)))


def _ole_or_iso_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("/Date("):
        match = re.search(r"/Date\((-?\d+)", text)
        if match:
            try:
                return (datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=int(match.group(1)))).date().isoformat()
            except OverflowError:
                return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text


def _normalize(result: dict[str, Any], requested: set[str]) -> tuple[list[dict[str, str]], dict[str, int]]:
    if result.get("responseException") is not None:
        raise ValueError(f"prebreakout_keydev_provider_exception:{result.get('responseException')}")
    rows = result.get("rows")
    if not isinstance(rows, list):
        raise ValueError("prebreakout_keydev_rows_required")
    output: list[dict[str, str]] = []
    covered: set[str] = set()
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError("prebreakout_keydev_row_shape_invalid")
        entities = row[6] if isinstance(row[6], list) else []
        event_entities: list[str] = []
        for item in entities:
            if not isinstance(item, list):
                continue
            candidates = [str(value) for value in item if str(value).isdigit()]
            matched = next((value for value in candidates if value in requested), None)
            if matched is not None:
                event_entities.append(matched)
        for entity in sorted(set(event_entities), key=int):
            covered.add(entity)
            output.append(
                {
                    "SP_ENTITY_ID": entity,
                    "EVENT_DATE": _ole_or_iso_date(row[0]),
                    "EVENT_OID": str(row[1] or "").strip(),
                    "EVENT_TYPE": str(row[2] or "").strip(),
                    "HEADLINE": str(row[3] or "").strip(),
                    "DESCRIPTION": str(row[4] or "").strip(),
                }
            )
    output.sort(key=lambda r: (int(r["SP_ENTITY_ID"]), r["EVENT_DATE"], r["EVENT_OID"]))
    return output, {"provider_row_count": len(rows), "normalized_entity_event_rows": len(output), "entities_with_any_event": len(covered)}


def _load_union_ids(paths: list[str]) -> list[str]:
    ids: set[str] = set()
    for pattern in paths:
        for path in sorted(Path().glob(pattern)):
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    entity = str(row.get("SP_ENTITY_ID") or "").strip()
                    if entity:
                        if not entity.isdigit():
                            raise ValueError(f"prebreakout_keydev_entity_invalid:{entity}")
                        ids.add(entity)
    if not ids:
        raise ValueError("prebreakout_keydev_union_empty")
    return sorted(ids, key=int)


async def capture(args: argparse.Namespace) -> None:
    entity_ids = _load_union_ids(args.corpus_glob)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parts: list[dict[str, Any]] = []
    async with Cdp(args.port) as cdp:
        for index, offset in enumerate(range(0, len(entity_ids), args.batch_size)):
            batch = entity_ids[offset : offset + args.batch_size]
            csv_path = out_dir / f"part_{index:03d}.csv"
            receipt_path = out_dir / f"part_{index:03d}.receipt.json"
            if csv_path.exists() or receipt_path.exists():
                if not args.resume or csv_path.is_file() != receipt_path.is_file():
                    raise FileExistsError(f"prebreakout_keydev_part_exists_or_partial:{index}")
                receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
                if receipt.get("raw_object_sha256") != _sha256(csv_path):
                    raise ValueError(f"prebreakout_keydev_resume_hash_mismatch:{index}")
                if receipt.get("requested_entity_ids") != batch:
                    raise ValueError(f"prebreakout_keydev_resume_membership_mismatch:{index}")
                parts.append({"index": index, "status": "REUSED", "csv": csv_path.name, "csv_sha256": _sha256(csv_path), "receipt": receipt_path.name, "receipt_sha256": _sha256(receipt_path), "requested_entity_count": len(batch)})
                print(f"PREBREAKOUT_KEYDEV_REUSED\tINDEX={index}\tENTITIES={len(batch)}", flush=True)
                continue
            result = await cdp.evaluate(_query_js(batch))
            rows, stats = _normalize(result, set(batch))
            _atomic_csv(csv_path, rows)
            retrieved = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
            receipt = {
                "schema_version": PART_SCHEMA,
                "family_id": FAMILY_ID,
                "w2_contract_sha256": W2_CONTRACT_SHA256,
                "source_id": "SPCIQPRO:KEY_DEVELOPMENTS_PRODUCTQUERY",
                "provider": PROVIDER,
                "perspective": PERSPECTIVE,
                "entity_filter_field": ENTITY_FILTER_FIELD,
                "event_date_field": EVENT_DATE_FIELD,
                "event_type_field": EVENT_TYPE_FIELD,
                "event_type_secondary_key": EVENT_TYPE_SECONDARY_KEY,
                "lifecycle_event_type_keys": list(LIFECYCLE_EVENT_TYPE_KEYS),
                "role_secondary_key": ROLE_SECONDARY_KEY,
                "role_secondary_value": ROLE_SECONDARY_VALUE,
                "requested_entity_ids": batch,
                "requested_entity_count": len(batch),
                "requested_entity_membership_sha256": hashlib.sha256(json.dumps(batch,separators=(",",":")).encode()).hexdigest(),
                "provider_row_count": stats["provider_row_count"],
                "normalized_entity_event_rows": stats["normalized_entity_event_rows"],
                "entities_with_any_event": stats["entities_with_any_event"],
                "retrieved_at": retrieved,
                "raw_object_name": csv_path.name,
                "raw_object_sha256": _sha256(csv_path),
                "raw_object_bytes": csv_path.stat().st_size,
                "existing_session_reused": True,
                "sign_in_performed": False,
                "sign_out_performed": False,
                "current_profile_state_used": False,
                "license_scope": LICENSE_SCOPE,
                "retention_class": RETENTION_CLASS,
                "outcome_access_performed": False,
                "financial_alpha_evidence": 0,
                "capital_authority": "NONE",
            }
            _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            parts.append({"index": index, "status": "CAPTURED", "csv": csv_path.name, "csv_sha256": _sha256(csv_path), "receipt": receipt_path.name, "receipt_sha256": _sha256(receipt_path), "requested_entity_count": len(batch)})
            print(f"PREBREAKOUT_KEYDEV_OK\tINDEX={index}\tENTITIES={len(batch)}\tEVENT_ROWS={len(rows)}\tSHA256={_sha256(csv_path)}", flush=True)
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "family_id": FAMILY_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "union_entity_count": len(entity_ids),
        "union_entity_membership_sha256": hashlib.sha256(json.dumps(entity_ids,separators=(",",":")).encode()).hexdigest(),
        "part_count": len(parts),
        "parts": parts,
        "provider": PROVIDER,
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    manifest_path = out_dir / "capture.manifest.json"
    _atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"PREBREAKOUT_KEYDEV_CAPTURE_OK\tENTITIES={len(entity_ids)}\tPARTS={len(parts)}\tMANIFEST_SHA256={_sha256(manifest_path)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--corpus-glob", action="append", required=True)
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 500:
        raise ValueError("prebreakout_keydev_batch_size_invalid")
    asyncio.run(capture(args))


if __name__ == "__main__":
    main()
