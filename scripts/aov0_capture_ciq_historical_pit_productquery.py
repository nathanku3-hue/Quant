"""Capture Lane-2 Original/as-of CIQ fundamentals through an existing web session.

This entrypoint never signs in, signs out, launches, or navigates Capital IQ Pro.
It attaches to an already-running Chromium DevTools target and submits scalar
SPG requests through the authenticated CIQ Pro page.  It can capture either the
weekly FQ0 period-end matrix or the sparse five-quarter fundamental transitions
consumed by the historical replay engine.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

import pandas as pd
import requests
import websockets


SOURCE_ID = "SPCIQPRO:SPG_PRODUCTQUERY_EXISTING_WEB_SESSION"
ENDPOINT = "/apisv3/ht/office-micro-data-service/v1/ProductQuery"
OPTIONS = "Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Original"
FILING_VERSION = "Original"
PROVIDER_FUNCTION = "SPG"
PERIOD_METRIC = "IQ_PERIOD_END"
PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")
TRANSITION_METRICS = (
    "IQ_PERIOD_END",
    "IQ_TOTAL_REV",
    "IQ_TOTAL_ASSETS",
    "IQ_INVENTORY",
    "IQ_DA_SUPPL_CF",
    "IQ_TOTAL_EQUITY",
    "IQ_TOTAL_DEBT",
    "IQ_CASH_ST_INVEST",
    "IQ_OPER_INC",
    "IQ_CAPEX_BNK",
)
S0_STRUCTURED_TRANSITION_METRICS = (
    "IQ_PERIOD_END",
    "IQ_TOTAL_REV",
    "IQ_INVENTORY",
    "IQ_OPER_INC",
    "IQ_CAPEX_BNK",
)
PERIOD_RECEIPT_SCHEMA = "aov0_ciq_productquery_historical_pit_period_matrix_receipt_v1"
TRANSITION_RECEIPT_SCHEMA = "aov0_ciq_productquery_historical_pit_transition_receipt_v1"


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
        if path.exists():
            raise FileExistsError(f"historical_pit_capture_output_exists:{path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _atomic_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("historical_pit_capture_rows_empty")
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
        if path.exists():
            raise FileExistsError(f"historical_pit_capture_output_exists:{path}")
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
            page["webSocketDebuggerUrl"],
            max_size=128 * 1024 * 1024,
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
            result = message.get("result", {}).get("result", {})
            if result.get("subtype") == "error":
                raise RuntimeError(result.get("description", result))
            return result.get("value")


def _conversion_information() -> dict[str, object]:
    return {
        "keyCurrency": "USD",
        "measurementStandard": 0,
        "conversionMode": 0,
        "magnitudeOverride": None,
        "keyForeignLanguage": None,
        "keyForeignLanguageSecondary": None,
        "dataLanguage": "en-US",
        "culture": None,
        "requestCulture": "en-US",
        "reportingBasis": "Original",
        "nullValue": "NA",
        "headerCurrency": "USD",
        "dataSource": "",
        "dateComparison": "Filing Date",
        "industryClassification": 0,
        "packageTrancheClassification": None,
    }


def _client_context() -> dict[str, object]:
    return {
        "templateId": None,
        "clientVersion": "1.0.26196.1",
        "machineId": "00000000-0000-0000-0000-000000000000",
        "disableLogging": False,
        "is64Bit": True,
        "keyClientCodes": None,
        "isGroup": False,
        "randomClientCodes": None,
        "excelCulture": "en-US",
        "includeDiagnostics": False,
        "ignoreCache": False,
        "requestSource": 0,
        "forceLocalQueries": False,
        "enableStatistics": False,
        "refreshId": "00000000-0000-0000-0000-000000000000",
    }


def _scalar_request(request_id: int, *, entity: str, metric: str, period: str, as_of: str) -> dict[str, object]:
    return {
        "id": int(request_id),
        "dispid": 12,
        "parameters": [
            str(entity),
            str(metric),
            str(period),
            pd.Timestamp(as_of).strftime("%m/%d/%Y"),
            OPTIONS,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    }


def _request_body(requests_payload: list[dict[str, object]]) -> dict[str, object]:
    return {
        "requests": requests_payload,
        "formatType": 0,
        "conversionInformation": _conversion_information(),
        "automaticRefresh": False,
        "committedRefresh": False,
        "clientContext": _client_context(),
        "userDefinedFormulas": [],
        "extensionPropertiesJson": None,
    }


def _fetch_expression(body: dict[str, object]) -> str:
    return f"""(async()=>{{
 const r=await fetch({json.dumps(ENDPOINT)},{{method:'POST',credentials:'include',headers:{{'Content-Type':'application/json','Accept':'application/json'}},body:JSON.stringify({json.dumps(body,separators=(',',':'))})}});
 const text=await r.text(); let parsed; try{{parsed=JSON.parse(text)}}catch{{parsed=text}}
 return {{status:r.status,statusText:r.statusText,contentType:r.headers.get('content-type'),body:parsed}};
}})()"""


def _extract_data(response: dict[str, object]) -> object:
    if response.get("error") is not None or response.get("responseException") is not None:
        raise ValueError(
            f"historical_pit_provider_error:id={response.get('id')}:"
            f"error={response.get('error')}:exception={response.get('responseException')}"
        )
    try:
        return response["result"][0][0][0].get("Data")  # type: ignore[index,union-attr]
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ValueError(f"historical_pit_provider_result_shape_invalid:id={response.get('id')}") from exc


def _missing(value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or text.upper() in {"NA", "N/A", "NAN", "NULL", "NONE", "#N/A", "#VALUE!", "#ERROR!"}


def _period_end(value: object) -> str:
    if _missing(value):
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if not math.isfinite(numeric):
            return ""
        # CIQ's scalar SPG transport returns Excel/OLE date serials for IQ_PERIOD_END.
        if 10_000 <= numeric <= 100_000:
            return (pd.Timestamp("1899-12-30") + pd.Timedelta(days=numeric)).date().isoformat()
    try:
        return pd.Timestamp(value).date().isoformat()
    except Exception as exc:
        raise ValueError(f"historical_pit_period_end_unparseable:{value!r}") from exc


def _numeric_text(value: object) -> str:
    if _missing(value):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).strip()
    if not math.isfinite(number):
        return ""
    return format(number, ".17g")


def _load_master(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    if "SP_ENTITY_ID" not in frame.columns:
        raise ValueError("historical_pit_master_missing_entity_id")
    entity = frame["SP_ENTITY_ID"].astype(str).str.strip()
    if entity.eq("").any() or entity.duplicated().any() or not entity.str.fullmatch(r"\d+").all():
        raise ValueError("historical_pit_master_entity_id_invalid")
    frame = frame.copy()
    frame["SP_ENTITY_ID"] = entity
    return frame.sort_values("SP_ENTITY_ID", key=lambda values: values.astype(int)).reset_index(drop=True)


def _chunks(values: list[dict[str, object]], size: int) -> Iterable[list[dict[str, object]]]:
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


async def _execute_requests(cdp: Cdp, requests_payload: list[dict[str, object]], *, batch_requests: int) -> dict[int, object]:
    output: dict[int, object] = {}
    for batch_index, batch in enumerate(_chunks(requests_payload, batch_requests)):
        value = await cdp.evaluate(_fetch_expression(_request_body(batch)))
        if not isinstance(value, dict):
            raise ValueError("historical_pit_productquery_transport_result_invalid")
        if int(value.get("status", -1)) != 200:
            raise ValueError(
                f"historical_pit_productquery_http:{value.get('status')}:"
                f"{str(value.get('body'))[:1000]}"
            )
        body = value.get("body")
        if not isinstance(body, dict):
            raise ValueError("historical_pit_productquery_body_invalid")
        responses = body.get("responses")
        if not isinstance(responses, list) or len(responses) != len(batch):
            raise ValueError(
                f"historical_pit_productquery_response_count_invalid:{len(responses or [])}/{len(batch)}"
            )
        for response in responses:
            if not isinstance(response, dict):
                raise ValueError("historical_pit_productquery_response_invalid")
            response_id = int(response.get("id"))
            if response_id in output:
                raise ValueError(f"historical_pit_productquery_duplicate_response_id:{response_id}")
            output[response_id] = _extract_data(response)
        print(
            f"SPG_BATCH_OK\tINDEX={batch_index}\tREQUESTS={len(batch)}\tRESPONSES={len(responses)}",
            flush=True,
        )
    if len(output) != len(requests_payload):
        raise ValueError(f"historical_pit_productquery_total_response_count_invalid:{len(output)}/{len(requests_payload)}")
    return output


def _capture_receipt(
    *,
    schema: str,
    out: Path,
    source_path: Path,
    master_path: Path,
    row_count: int,
    retrieved_at: str,
    mode: str,
    extra: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": schema,
        "source_id": SOURCE_ID,
        "provider": "S&P Capital IQ Pro authenticated existing web session",
        "capture_mode": mode,
        "provider_endpoint": ENDPOINT,
        "provider_function": PROVIDER_FUNCTION,
        "filing_version": FILING_VERSION,
        "options": OPTIONS,
        "captured_at_utc": retrieved_at,
        "raw_object_name": out.name,
        "raw_object_sha256": _sha256(out),
        "raw_object_bytes": out.stat().st_size,
        "raw_grid_rows": row_count,
        "source_plan_name": source_path.name,
        "source_plan_sha256": _sha256(source_path),
        "master_name": master_path.name,
        "master_sha256": _sha256(master_path),
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        **extra,
    }


def _period_probe_pairs(plan: pd.DataFrame, master: pd.DataFrame) -> tuple[list[tuple[pd.Timestamp, str]], str]:
    if plan.empty or "as_of_date" not in plan.columns:
        raise ValueError("historical_pit_period_plan_invalid")
    valid_entities = set(master["SP_ENTITY_ID"].tolist())
    if list(plan.columns) == ["as_of_date"]:
        dates = [pd.Timestamp(value).normalize() for value in plan["as_of_date"].tolist()]
        if len(set(dates)) != len(dates):
            raise ValueError("historical_pit_period_plan_duplicate_date")
        return [(date, entity) for date in dates for entity in master["SP_ENTITY_ID"].tolist()], "DATE_CARTESIAN"
    if "source_entity_id" not in plan.columns:
        raise ValueError("historical_pit_period_plan_invalid")
    pairs: list[tuple[pd.Timestamp, str]] = []
    seen: set[tuple[pd.Timestamp, str]] = set()
    for row in plan.itertuples(index=False):
        entity = str(row.source_entity_id).strip()
        date = pd.Timestamp(row.as_of_date).normalize()
        if entity not in valid_entities:
            raise ValueError(f"historical_pit_period_plan_entity_outside_master:{entity}")
        key = (date, entity)
        if key in seen:
            raise ValueError(f"historical_pit_period_plan_duplicate_pair:{entity}:{date.date().isoformat()}")
        seen.add(key)
        pairs.append(key)
    pairs.sort(key=lambda item: (item[0], int(item[1])))
    return pairs, "EXACT_ENTITY_DATE_PAIRS"


def _requested_transition_metrics(args: argparse.Namespace) -> tuple[str, ...]:
    requested = tuple(str(value).strip().upper() for value in (getattr(args, "metric", None) or ()))
    if not requested:
        return TRANSITION_METRICS
    if len(requested) != len(set(requested)):
        raise ValueError("historical_pit_transition_metrics_duplicate")
    unknown = sorted(set(requested) - set(TRANSITION_METRICS))
    if unknown:
        raise ValueError("historical_pit_transition_metric_not_allowed:" + unknown[0])
    if PERIOD_METRIC not in requested:
        raise ValueError("historical_pit_transition_period_metric_required")
    return requested


async def capture_period_matrix(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    master_path = Path(args.master)
    out = Path(args.out)
    if out.exists() or out.with_suffix(".receipt.json").exists():
        raise FileExistsError(f"historical_pit_capture_output_exists:{out}")
    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    master = _load_master(master_path)
    pairs, plan_mode = _period_probe_pairs(plan, master)
    if not pairs:
        raise ValueError("historical_pit_period_plan_invalid")

    request_meta: dict[int, tuple[pd.Timestamp, str]] = {}
    payloads: list[dict[str, object]] = []
    request_id = 1
    for date, entity in pairs:
        payloads.append(
            _scalar_request(
                request_id,
                entity=entity,
                metric=PERIOD_METRIC,
                period="FQ0",
                as_of=date.date().isoformat(),
            )
        )
        request_meta[request_id] = (date, entity)
        request_id += 1

    async with Cdp(args.port) as cdp:
        values = await _execute_requests(cdp, payloads, batch_requests=args.batch_requests)
    retrieved_at = datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = []
    missing: list[tuple[str, str]] = []
    for response_id in sorted(request_meta):
        date, entity = request_meta[response_id]
        period_end = _period_end(values[response_id])
        if not period_end:
            missing.append((entity, date.date().isoformat()))
        rows.append(
            {
                "as_of_date": date.date().isoformat(),
                "source_entity_id": entity,
                "fq0_period_end": period_end,
                "retrieved_at_utc": retrieved_at,
                "provider_function": PROVIDER_FUNCTION,
                "provider_metric": PERIOD_METRIC,
                "relative_period": "FQ0",
                "filing_version": FILING_VERSION,
            }
        )
    if missing and not bool(getattr(args, "allow_missing_period_end", False)):
        entity, date = missing[0]
        raise ValueError(f"historical_pit_period_matrix_fq0_missing:{entity}:{date}:count={len(missing)}")
    rows.sort(key=lambda row: (str(row["as_of_date"]), int(str(row["source_entity_id"]))))
    _atomic_csv(out, rows)
    receipt_path = out.with_suffix(".receipt.json")
    receipt = _capture_receipt(
        schema=PERIOD_RECEIPT_SCHEMA,
        out=out,
        source_path=plan_path,
        master_path=master_path,
        row_count=len(rows),
        retrieved_at=retrieved_at,
        mode="HISTORICAL_PIT_WEEKLY_FQ0_PERIOD_MATRIX",
        extra={
            "weekly_date_count": len({date for date, _ in pairs}),
            "entity_count": len({entity for _, entity in pairs}),
            "probe_pair_count": len(pairs),
            "period_probe_plan_mode": plan_mode,
            "missing_fq0_period_end_count": len(missing),
            "missing_fq0_period_end_allowed": bool(getattr(args, "allow_missing_period_end", False)),
            "provider_metric": PERIOD_METRIC,
            "relative_period": "FQ0",
        },
    )
    _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        f"PERIOD_MATRIX_CAPTURE_OK\tDATES={len({date for date, _ in pairs})}"
        f"\tENTITIES={len({entity for _, entity in pairs})}\tPAIRS={len(pairs)}"
        f"\tMISSING_FQ0={len(missing)}\tROWS={len(rows)}\tSHA256={_sha256(out)}\tPATH={out}",
        flush=True,
    )


async def capture_transitions(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    master_path = Path(args.master)
    out = Path(args.out)
    if out.exists() or out.with_suffix(".receipt.json").exists():
        raise FileExistsError(f"historical_pit_capture_output_exists:{out}")
    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    master = _load_master(master_path)
    required = {"source_entity_id", "as_of_date"}
    if plan.empty or not required.issubset(plan.columns):
        raise ValueError("historical_pit_transition_plan_invalid")
    valid_entities = set(master["SP_ENTITY_ID"].tolist())
    pairs: list[tuple[str, pd.Timestamp]] = []
    observed_pairs: set[tuple[str, pd.Timestamp]] = set()
    for row in plan.itertuples(index=False):
        entity = str(row.source_entity_id).strip()
        date = pd.Timestamp(row.as_of_date).normalize()
        if entity not in valid_entities:
            raise ValueError(f"historical_pit_transition_entity_outside_master:{entity}")
        key = (entity, date)
        if key in observed_pairs:
            raise ValueError(f"historical_pit_transition_plan_duplicate:{entity}:{date.date().isoformat()}")
        observed_pairs.add(key)
        pairs.append(key)
    pairs.sort(key=lambda item: (item[1], int(item[0])))
    transition_metrics = _requested_transition_metrics(args)

    request_meta: dict[int, tuple[str, pd.Timestamp, str, str]] = {}
    payloads: list[dict[str, object]] = []
    request_id = 1
    for entity, date in pairs:
        for period in PERIODS:
            for metric in transition_metrics:
                payloads.append(
                    _scalar_request(
                        request_id,
                        entity=entity,
                        metric=metric,
                        period=period,
                        as_of=date.date().isoformat(),
                    )
                )
                request_meta[request_id] = (entity, date, period, metric)
                request_id += 1

    async with Cdp(args.port) as cdp:
        values = await _execute_requests(cdp, payloads, batch_requests=args.batch_requests)
    retrieved_at = datetime.now(UTC).isoformat()
    keyed: dict[tuple[str, pd.Timestamp, str], dict[str, object]] = {}
    for response_id in sorted(request_meta):
        entity, date, period, metric = request_meta[response_id]
        row = keyed.setdefault(
            (entity, date, period),
            {
                "as_of_date": date.date().isoformat(),
                "source_entity_id": entity,
                "relative_period": period,
                "period_end": "",
                **{name: "" for name in transition_metrics if name != "IQ_PERIOD_END"},
                "retrieved_at_utc": retrieved_at,
                "provider_function": PROVIDER_FUNCTION,
                "filing_version": FILING_VERSION,
            },
        )
        raw = values[response_id]
        if metric == "IQ_PERIOD_END":
            row["period_end"] = _period_end(raw)
        else:
            row[metric] = _numeric_text(raw)
    rows = list(keyed.values())
    period_order = {period: index for index, period in enumerate(PERIODS)}
    rows.sort(
        key=lambda row: (
            str(row["as_of_date"]),
            int(str(row["source_entity_id"])),
            period_order[str(row["relative_period"])],
        )
    )
    fq0_missing = [row for row in rows if row["relative_period"] == "FQ0" and not row["period_end"]]
    if fq0_missing:
        first = fq0_missing[0]
        raise ValueError(
            "historical_pit_transition_fq0_missing:"
            f"{first['source_entity_id']}:{first['as_of_date']}:count={len(fq0_missing)}"
        )
    if len(rows) != len(pairs) * len(PERIODS):
        raise ValueError(f"historical_pit_transition_output_grid_invalid:{len(rows)}/{len(pairs)*len(PERIODS)}")
    _atomic_csv(out, rows)
    receipt_path = out.with_suffix(".receipt.json")
    receipt = _capture_receipt(
        schema=TRANSITION_RECEIPT_SCHEMA,
        out=out,
        source_path=plan_path,
        master_path=master_path,
        row_count=len(rows),
        retrieved_at=retrieved_at,
        mode="HISTORICAL_PIT_SPARSE_ORIGINAL_FUNDAMENTAL_TRANSITIONS",
        extra={
            "transition_count": len(pairs),
            "relative_periods": list(PERIODS),
            "metrics": list(transition_metrics),
        },
    )
    _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        f"TRANSITION_CAPTURE_OK\tTRANSITIONS={len(pairs)}\tROWS={len(rows)}"
        f"\tSHA256={_sha256(out)}\tPATH={out}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--batch-requests", type=int, default=200)
    sub = parser.add_subparsers(dest="command", required=True)

    period = sub.add_parser("period-matrix")
    period.add_argument("--plan", required=True)
    period.add_argument("--master", required=True)
    period.add_argument("--out", required=True)
    period.add_argument("--allow-missing-period-end", action="store_true")

    transitions = sub.add_parser("transitions")
    transitions.add_argument("--plan", required=True)
    transitions.add_argument("--master", required=True)
    transitions.add_argument("--out", required=True)
    transitions.add_argument(
        "--metric",
        action="append",
        help="Repeat to restrict sparse transition capture to an exact allowed metric subset; IQ_PERIOD_END is mandatory.",
    )

    args = parser.parse_args()
    if args.batch_requests < 1 or args.batch_requests > 500:
        raise ValueError("batch_requests_out_of_range:1..500")
    if args.command == "period-matrix":
        asyncio.run(capture_period_matrix(args))
    else:
        asyncio.run(capture_transitions(args))


if __name__ == "__main__":
    main()
