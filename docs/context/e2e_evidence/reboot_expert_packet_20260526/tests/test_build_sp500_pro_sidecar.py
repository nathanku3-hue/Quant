from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import pytest

from scripts import build_sp500_pro_sidecar as mod


def _make_minimal_security_detail_workbook(path: Path) -> None:
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Security Detail" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""
    shared_strings_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="7" uniqueCount="7">
  <si><t>Avantax, Inc.</t></si>
  <si><t>AVTA</t></si>
  <si><t>US0952291005</t></si>
  <si><t>95229100</t></si>
  <si><t>Company Name</t></si>
  <si><t>Trading Symbol</t></si>
  <si><t>ISIN</t></si>
</sst>
"""
    sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="7">
      <c r="A7" t="s"><v>4</v></c>
      <c r="C7" t="s"><v>0</v></c>
    </row>
    <row r="9">
      <c r="A9" t="s"><v>5</v></c>
      <c r="C9" t="s"><v>1</v></c>
      <c r="J9"><v>36144</v></c>
    </row>
    <row r="10">
      <c r="A10" t="s"><v>6</v></c>
      <c r="C10" t="s"><v>2</v></c>
    </row>
    <row r="11">
      <c r="C11" t="s"><v>3</v></c>
    </row>
    <row r="23">
      <c r="E23"><v>45236</v></c>
    </row>
  </sheetData>
</worksheet>
"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        zf.writestr("xl/sharedStrings.xml", shared_strings_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def test_extract_security_detail_metadata_reads_expected_cells(tmp_path: Path) -> None:
    workbook_path = tmp_path / "security_detail.xlsx"
    _make_minimal_security_detail_workbook(workbook_path)

    metadata = mod.extract_security_detail_metadata(workbook_path)

    assert metadata["company_name"] == "Avantax, Inc."
    assert metadata["ticker"] == "AVTA"
    assert metadata["isin"] == "US0952291005"
    assert metadata["cusip_raw"] == "95229100"
    assert pd.Timestamp(metadata["date"]) == pd.Timestamp("2023-11-06")
    assert pd.Timestamp(metadata["issue_date"]) == pd.Timestamp("1998-12-15")


def test_build_sp500_pro_sidecar_joins_map_and_applies_date_mask(tmp_path: Path) -> None:
    workbook_path = tmp_path / "security_detail.xlsx"
    _make_minimal_security_detail_workbook(workbook_path)
    map_path = tmp_path / "permno_cusip.csv"
    pd.DataFrame({"PERMNO": [86544], "CUSIP": ["095229100"]}).to_csv(map_path, index=False)

    sidecar, summary = mod.build_sp500_pro_sidecar(
        workbook_path=workbook_path,
        mapping_path=map_path,
        tape_csv_path=tmp_path / "missing.csv",
        date_mask_start=pd.Timestamp("2023-01-01"),
        allow_metadata_fallback=True,
    )

    assert list(sidecar.columns[:6]) == ["date", "permno", "sp_rating", "sp_score", "price", "total_return"]
    assert len(sidecar) == 1
    assert sidecar.loc[0, "permno"] == 86544
    assert sidecar.loc[0, "cusip"] == "095229100"
    assert sidecar.loc[0, "isin"] == "US0952291005"
    assert pd.Timestamp(sidecar.loc[0, "date"]) == pd.Timestamp("2023-11-06")
    assert sidecar.loc[0, "price"] is pd.NA
    assert sidecar.loc[0, "total_return"] is pd.NA
    assert summary["rows_after_mask"] == 1
    assert summary["matched_permnos"] == [86544]


def test_cusip_join_candidates_handles_true_base_and_excel_stripped_numeric() -> None:
    assert "095229100" in mod._cusip_join_candidates("09522910", None)
    assert "095229100" in mod._cusip_join_candidates("95229100", None)


def test_build_sp500_pro_sidecar_fails_closed_when_date_mask_removes_all_rows(tmp_path: Path) -> None:
    workbook_path = tmp_path / "security_detail.xlsx"
    _make_minimal_security_detail_workbook(workbook_path)
    map_path = tmp_path / "permno_cusip.csv"
    pd.DataFrame({"PERMNO": [86544], "CUSIP": ["095229100"]}).to_csv(map_path, index=False)

    with pytest.raises(RuntimeError, match="Strict date mask removed every sidecar row"):
        mod.build_sp500_pro_sidecar(
            workbook_path=workbook_path,
            mapping_path=map_path,
            tape_csv_path=tmp_path / "missing.csv",
            date_mask_start=pd.Timestamp("2024-01-01"),
            allow_metadata_fallback=True,
        )


def test_build_sp500_pro_sidecar_prefers_raw_tape_csv(tmp_path: Path) -> None:
    workbook_path = tmp_path / "security_detail.xlsx"
    _make_minimal_security_detail_workbook(workbook_path)
    map_path = tmp_path / "permno_cusip.csv"
    pd.DataFrame({"PERMNO": [86544], "CUSIP": ["095229100"]}).to_csv(map_path, index=False)
    tape_path = tmp_path / "sp500_pro_avantax_tape.csv"
    pd.DataFrame(
        {
            "Date": ["2022-12-30", "2023-01-03", "2023-11-06"],
            "Price": [10.0, 11.0, 25.99],
            "Total_Return": [0.01, 0.02, -0.03],
        }
    ).to_csv(tape_path, index=False)

    sidecar, summary = mod.build_sp500_pro_sidecar(
        workbook_path=workbook_path,
        mapping_path=map_path,
        tape_csv_path=tape_path,
        date_mask_start=pd.Timestamp("2023-01-01"),
    )

    assert summary["metadata_mode"] == "raw_tape_csv"
    assert summary["rows_before_mask"] == 3
    assert summary["rows_after_mask"] == 2
    assert summary["price_present"] is True
    assert summary["total_return_present"] is True
    assert sidecar["date"].dt.strftime("%Y-%m-%d").tolist() == ["2023-01-03", "2023-11-06"]
    assert sidecar["permno"].astype(int).tolist() == [86544, 86544]
    assert sidecar["cusip"].tolist() == ["095229100", "095229100"]
    assert sidecar["price"].tolist() == [11.0, 25.99]
    assert sidecar["total_return"].tolist() == [0.02, -0.03]


def test_build_sp500_pro_sidecar_blocks_when_raw_tape_missing_by_default(tmp_path: Path) -> None:
    workbook_path = tmp_path / "security_detail.xlsx"
    _make_minimal_security_detail_workbook(workbook_path)
    map_path = tmp_path / "permno_cusip.csv"
    pd.DataFrame({"PERMNO": [86544], "CUSIP": ["095229100"]}).to_csv(map_path, index=False)

    with pytest.raises(RuntimeError, match="Raw tape CSV is missing"):
        mod.build_sp500_pro_sidecar(
            workbook_path=workbook_path,
            mapping_path=map_path,
            tape_csv_path=tmp_path / "missing.csv",
            date_mask_start=pd.Timestamp("2023-01-01"),
        )


def test_load_raw_tape_csv_rejects_duplicate_dates(tmp_path: Path) -> None:
    tape_path = tmp_path / "sp500_pro_avantax_tape.csv"
    pd.DataFrame(
        {
            "Date": ["2023-01-03", "2023-01-03"],
            "Price": [11.0, 11.1],
            "Total_Return": [0.02, 0.03],
        }
    ).to_csv(tape_path, index=False)

    with pytest.raises(RuntimeError, match="duplicate dates"):
        mod._load_raw_tape_csv(tape_path)


def test_load_raw_tape_csv_rejects_all_nan_numeric_columns_and_parses_parentheses(tmp_path: Path) -> None:
    tape_path = tmp_path / "sp500_pro_avantax_tape.csv"
    pd.DataFrame(
        {
            "Date": ["2023-01-03", "2023-01-04"],
            "Price": ["(11.00)", "(10.50)"],
            "Total_Return": ["(2.00%)", "(3.50%)"],
        }
    ).to_csv(tape_path, index=False)

    tape = mod._load_raw_tape_csv(tape_path)
    assert tape["price"].tolist() == [-11.0, -10.5]
    assert tape["total_return"].tolist() == [-0.02, -0.035]

    bad_tape_path = tmp_path / "bad_sp500_pro_avantax_tape.csv"
    pd.DataFrame(
        {
            "Date": ["2023-01-03", "2023-01-04"],
            "Price": ["bad", "bad"],
            "Total_Return": ["bad", "bad"],
        }
    ).to_csv(bad_tape_path, index=False)

    with pytest.raises(RuntimeError, match="no parseable price values"):
        mod._load_raw_tape_csv(bad_tape_path)
