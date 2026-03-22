from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK_PATH = PROJECT_ROOT / "SPGlobal_Avantax,Inc._SecurityDetail_19-Mar-2026.xlsx"
DEFAULT_MAP_PATH = PROJECT_ROOT / "data" / "processed" / "d341_missing_executed_exposure_permno_cusip.csv"
DEFAULT_TAPE_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "sp500_pro_avantax_tape.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "sidecar_sp500_pro_2023_2024.parquet"
RUN_DATE_TAG = pd.Timestamp.now().strftime("%Y%m%d")
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "docs" / "context" / "e2e_evidence" / f"phase61_sp500_pro_sidecar_{RUN_DATE_TAG}_summary.json"
)
DEFAULT_DATE_MASK_START = pd.Timestamp("2023-01-01")

XML_NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(frozen=True)
class CellValue:
    ref: str
    raw: str | None
    rendered: str | None


def _atomic_write_parquet(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_parquet(temp_path, index=False)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _atomic_write_json(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _load_shared_strings(zf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    sst = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in sst.findall("x:si", XML_NS):
        parts = [t.text or "" for t in si.iterfind(".//x:t", XML_NS)]
        values.append("".join(parts))
    return values


def _sheet_target(zf: ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pr:Relationship", XML_NS)}
    sheets = workbook.find("x:sheets", XML_NS)
    if sheets is None:
        raise RuntimeError("Workbook is missing sheet definitions.")
    for sheet in sheets:
        if sheet.attrib.get("name") != sheet_name:
            continue
        rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        if rel_id is None or rel_id not in rel_map:
            raise RuntimeError(f"Workbook sheet {sheet_name!r} is missing a relationship target.")
        target = rel_map[rel_id]
        return target if target.startswith("xl/") else f"xl/{target}"
    raise RuntimeError(f"Workbook sheet {sheet_name!r} not found.")


def _load_sheet_cells(workbook_path: Path, sheet_name: str = "Security Detail") -> dict[str, CellValue]:
    with ZipFile(workbook_path) as zf:
        target = _sheet_target(zf, sheet_name)
        shared = _load_shared_strings(zf)
        ws = ET.fromstring(zf.read(target))

    cells: dict[str, CellValue] = {}
    for cell in ws.findall(".//x:sheetData/x:row/x:c", XML_NS):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        raw_node = cell.find("x:v", XML_NS)
        raw = raw_node.text if raw_node is not None else None
        rendered = raw
        cell_type = cell.attrib.get("t")
        inline = cell.find("x:is", XML_NS)
        if cell_type == "s" and raw is not None:
            rendered = shared[int(raw)]
        elif inline is not None:
            rendered = "".join((t.text or "") for t in inline.iterfind(".//x:t", XML_NS))
        cells[ref] = CellValue(ref=ref, raw=raw, rendered=rendered)
    return cells


def excel_serial_to_timestamp(serial: str | float | int | None) -> pd.Timestamp:
    if serial in (None, ""):
        raise ValueError("Excel serial date is missing.")
    base = pd.Timestamp("1899-12-30")
    return base + pd.to_timedelta(float(serial), unit="D")


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    out = str(value).strip()
    return out or None


def _normalize_cusip9(value: str | None) -> str | None:
    text = _normalize_text(value)
    if text is None:
        return None
    text = "".join(ch for ch in text.upper() if ch.isalnum())
    return text or None


def _cusip9_from_isin(isin: str | None) -> str | None:
    text = _normalize_text(isin)
    if text is None:
        return None
    text = text.upper()
    if len(text) == 12 and text[:2].isalpha():
        return text[2:11]
    return None


def _cusip_check_digit(cusip_base: str) -> str:
    total = 0
    for index, char in enumerate(cusip_base, start=1):
        if char.isdigit():
            value = int(char)
        elif "A" <= char <= "Z":
            value = ord(char) - ord("A") + 10
        elif char == "*":
            value = 36
        elif char == "@":
            value = 37
        elif char == "#":
            value = 38
        else:
            raise ValueError(f"Unsupported CUSIP character: {char}")
        if index % 2 == 0:
            value *= 2
        total += (value // 10) + (value % 10)
    return str((10 - (total % 10)) % 10)


def _cusip_join_candidates(raw_cusip: str | None, isin: str | None) -> set[str]:
    candidates: set[str] = set()
    isin_cusip9 = _cusip9_from_isin(isin)
    if isin_cusip9 is not None:
        candidates.add(isin_cusip9)

    raw = _normalize_cusip9(raw_cusip)
    if raw is None:
        return candidates

    if len(raw) == 9:
        candidates.add(raw)
        return candidates

    if len(raw) == 8:
        try:
            candidates.add(raw + _cusip_check_digit(raw))
        except ValueError:
            pass
        if raw.isdigit():
            candidates.add(raw.zfill(9))
        return candidates

    if raw.isdigit() and len(raw) < 8:
        candidates.add(raw.zfill(9))
    return candidates


def extract_security_detail_metadata(workbook_path: Path) -> dict[str, object]:
    cells = _load_sheet_cells(workbook_path, sheet_name="Security Detail")
    if "E23" not in cells:
        raise RuntimeError("Security Detail workbook is missing the expected As Of cell (E23).")
    metadata = {
        "company_name": _normalize_text(cells.get("C7", CellValue("C7", None, None)).rendered),
        "ticker": _normalize_text(cells.get("C9", CellValue("C9", None, None)).rendered),
        "isin": _normalize_text(cells.get("C10", CellValue("C10", None, None)).rendered),
        "cusip_raw": _normalize_cusip9(cells.get("C11", CellValue("C11", None, None)).rendered),
        "issue_date": excel_serial_to_timestamp(cells.get("J9", CellValue("J9", None, None)).raw),
        "date": excel_serial_to_timestamp(cells["E23"].raw),
        "source_file": str(workbook_path),
        "source_sheet": "Security Detail",
    }
    return metadata


def _load_permno_cusip_map(mapping_path: Path) -> pd.DataFrame:
    if not mapping_path.exists():
        raise FileNotFoundError(f"Missing PERMNO/CUSIP map: {mapping_path}")
    if mapping_path.suffix.lower() == ".parquet":
        mapping = pd.read_parquet(mapping_path)
    else:
        mapping = pd.read_csv(mapping_path, dtype={"PERMNO": "string", "CUSIP": "string"})
    required = {"PERMNO", "CUSIP"}
    missing = required - set(mapping.columns)
    if missing:
        raise ValueError(f"PERMNO/CUSIP map missing required columns: {sorted(missing)}")
    mapping = mapping.copy()
    mapping["PERMNO"] = pd.to_numeric(mapping["PERMNO"], errors="coerce").astype("Int64")
    mapping["CUSIP"] = mapping["CUSIP"].astype(str).str.upper().str.strip()
    mapping = mapping.dropna(subset=["PERMNO", "CUSIP"]).drop_duplicates(subset=["PERMNO", "CUSIP"]).reset_index(drop=True)
    return mapping


def _normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    has_percent = text.str.contains("%", regex=False, na=False)
    is_parenthesized = text.str.match(r"^\(.*\)$", na=False)
    cleaned = (
        text.str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NA": pd.NA})
    )
    numeric = pd.to_numeric(cleaned, errors="coerce")
    numeric = numeric.where(~is_parenthesized, -numeric.abs())
    if has_percent.any():
        numeric = numeric.where(~has_percent, numeric / 100.0)
    return numeric


def _load_raw_tape_csv(tape_csv_path: Path) -> pd.DataFrame:
    if not tape_csv_path.exists():
        raise FileNotFoundError(f"Missing raw tape CSV: {tape_csv_path}")
    raw = pd.read_csv(tape_csv_path)
    normalized_columns = {_normalize_name(col): col for col in raw.columns}
    required_keys = {"date", "price", "totalreturn"}
    missing = required_keys - set(normalized_columns)
    if missing:
        raise ValueError(
            f"Raw tape CSV missing required columns after normalization: {sorted(missing)}; "
            f"found={list(raw.columns)}"
        )
    tape = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[normalized_columns["date"]], errors="coerce").dt.normalize(),
            "price": _coerce_numeric_series(raw[normalized_columns["price"]]),
            "total_return": _coerce_numeric_series(raw[normalized_columns["totalreturn"]]),
        }
    )
    tape = tape.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if tape["date"].duplicated().any():
        duplicates = tape.loc[tape["date"].duplicated(keep=False), "date"].dt.strftime("%Y-%m-%d").tolist()
        raise RuntimeError(f"Raw tape CSV contains duplicate dates: {duplicates}")
    if tape["price"].notna().sum() == 0:
        raise RuntimeError("Raw tape CSV has no parseable price values.")
    if tape["total_return"].notna().sum() == 0:
        raise RuntimeError("Raw tape CSV has no parseable total_return values.")
    return tape


def build_sp500_pro_sidecar(
    *,
    workbook_path: Path,
    mapping_path: Path,
    tape_csv_path: Path | None = None,
    date_mask_start: pd.Timestamp = DEFAULT_DATE_MASK_START,
    allow_metadata_fallback: bool = False,
) -> tuple[pd.DataFrame, dict[str, object]]:
    metadata = extract_security_detail_metadata(workbook_path)
    mapping = _load_permno_cusip_map(mapping_path)

    candidate_cusips = _cusip_join_candidates(
        metadata.get("cusip_raw"),  # type: ignore[arg-type]
        metadata.get("isin"),  # type: ignore[arg-type]
    )
    if not candidate_cusips:
        raise RuntimeError("Workbook did not expose a usable CUSIP/ISIN identifier.")

    matched = mapping[mapping["CUSIP"].isin(candidate_cusips)].copy()
    if matched.empty:
        raise RuntimeError(
            f"No PERMNO/CUSIP map match found for workbook identifiers: {sorted(candidate_cusips)}"
        )
    if len(matched) > 1:
        raise RuntimeError(
            f"Ambiguous PERMNO/CUSIP mapping for workbook identifiers {sorted(candidate_cusips)}: "
            f"{matched.to_dict(orient='records')}"
        )

    match = matched.iloc[0]
    matched_cusip = str(match["CUSIP"])
    tape_csv_path = tape_csv_path or DEFAULT_TAPE_CSV_PATH

    if tape_csv_path.exists():
        tape = _load_raw_tape_csv(tape_csv_path)
        tape = tape.copy()
        tape["cusip"] = matched_cusip
        tape = tape.merge(
            mapping.rename(columns={"PERMNO": "permno", "CUSIP": "cusip"}),
            on="cusip",
            how="left",
            validate="many_to_one",
        )
        tape["permno"] = pd.to_numeric(tape["permno"], errors="coerce").astype("Int64")
        if tape["permno"].isna().any():
            raise RuntimeError("Tape CSV join did not resolve PERMNO for every row.")
        tape["sp_rating"] = pd.NA
        tape["sp_score"] = pd.NA
        tape["isin"] = metadata["isin"]
        tape["ticker"] = metadata["ticker"]
        tape["company_name"] = metadata["company_name"]
        tape["issue_date"] = pd.Timestamp(metadata["issue_date"]).normalize()
        tape["source_as_of_date"] = pd.Timestamp(metadata["date"]).normalize()
        tape["source_file"] = str(tape_csv_path)
        tape["source_sheet"] = "raw_csv"
        sidecar = tape[
            [
                "date",
                "permno",
                "sp_rating",
                "sp_score",
                "price",
                "total_return",
                "cusip",
                "isin",
                "ticker",
                "company_name",
                "issue_date",
                "source_as_of_date",
                "source_file",
                "source_sheet",
            ]
        ].copy()
        source_mode = "raw_tape_csv"
        rows_before_mask = int(len(sidecar))
    else:
        if not allow_metadata_fallback:
            raise RuntimeError(
                f"Raw tape CSV is missing at {tape_csv_path}; "
                "D-350 daily-tape remediation remains blocked until the literal CSV export is available."
            )
        row = {
            "date": pd.Timestamp(metadata["date"]).normalize(),
            "permno": int(match["PERMNO"]),
            "sp_rating": pd.NA,
            "sp_score": pd.NA,
            "price": pd.NA,
            "total_return": pd.NA,
            "cusip": matched_cusip,
            "isin": metadata["isin"],
            "ticker": metadata["ticker"],
            "company_name": metadata["company_name"],
            "issue_date": pd.Timestamp(metadata["issue_date"]).normalize(),
            "source_as_of_date": pd.Timestamp(metadata["date"]).normalize(),
            "source_file": metadata["source_file"],
            "source_sheet": metadata["source_sheet"],
        }
        sidecar = pd.DataFrame([row])
        source_mode = "security_detail_as_of_fallback"
        rows_before_mask = 1

    sidecar["date"] = pd.to_datetime(sidecar["date"], errors="coerce")
    sidecar["issue_date"] = pd.to_datetime(sidecar["issue_date"], errors="coerce")
    sidecar["source_as_of_date"] = pd.to_datetime(sidecar["source_as_of_date"], errors="coerce")
    sidecar = sidecar[sidecar["date"] >= pd.Timestamp(date_mask_start)].reset_index(drop=True)
    if sidecar.empty:
        raise RuntimeError(
            f"Strict date mask removed every sidecar row for workbook {workbook_path} "
            f"with date_mask_start={pd.Timestamp(date_mask_start).date()}."
        )

    summary = {
        "input_workbook": str(workbook_path),
        "input_map": str(mapping_path),
        "input_tape_csv": str(tape_csv_path),
        "date_mask_start": str(pd.Timestamp(date_mask_start).date()),
        "rows_before_mask": rows_before_mask,
        "rows_after_mask": int(len(sidecar)),
        "matched_permnos": sorted(sidecar["permno"].dropna().astype(int).unique().tolist()) if not sidecar.empty else [],
        "matched_cusips": sorted(sidecar["cusip"].dropna().astype(str).unique().tolist()) if not sidecar.empty else [],
        "source_date_min": str(sidecar["date"].min().date()) if not sidecar.empty else None,
        "source_date_max": str(sidecar["date"].max().date()) if not sidecar.empty else None,
        "metadata_mode": source_mode,
        "sp_rating_present": bool(sidecar["sp_rating"].notna().any()) if not sidecar.empty else False,
        "sp_score_present": bool(sidecar["sp_score"].notna().any()) if not sidecar.empty else False,
        "price_present": bool(sidecar["price"].notna().any()) if not sidecar.empty else False,
        "total_return_present": bool(sidecar["total_return"].notna().any()) if not sidecar.empty else False,
        "notes": [
            "The builder prefers the raw daily tape CSV when present and otherwise falls back to the metadata-only Security Detail workbook.",
            "The strict D-350 bound remains date >= 2023-01-01 in all modes.",
            "sp_rating and sp_score remain null unless a machine-readable vendor field is supplied.",
        ],
    }
    return sidecar, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the bounded S&P 500 Pro sidecar from a Security Detail workbook.")
    parser.add_argument("--input-workbook", default=str(DEFAULT_WORKBOOK_PATH))
    parser.add_argument("--permno-cusip-map", default=str(DEFAULT_MAP_PATH))
    parser.add_argument("--input-tape-csv", default=str(DEFAULT_TAPE_CSV_PATH))
    parser.add_argument("--date-mask-start", default=str(DEFAULT_DATE_MASK_START.date()))
    parser.add_argument("--output-parquet", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--output-summary-json", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument(
        "--allow-metadata-fallback",
        action="store_true",
        help="Allow the one-row Security Detail fallback when the raw tape CSV is absent.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sidecar, summary = build_sp500_pro_sidecar(
        workbook_path=Path(args.input_workbook),
        mapping_path=Path(args.permno_cusip_map),
        tape_csv_path=Path(args.input_tape_csv),
        date_mask_start=pd.Timestamp(args.date_mask_start),
        allow_metadata_fallback=bool(args.allow_metadata_fallback),
    )
    output_path = Path(args.output_parquet)
    summary_path = Path(args.output_summary_json)
    _atomic_write_parquet(sidecar, output_path)
    summary["output_parquet"] = str(output_path)
    summary["run_date_tag"] = RUN_DATE_TAG
    summary["output_columns"] = list(sidecar.columns)
    _atomic_write_json(summary, summary_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
