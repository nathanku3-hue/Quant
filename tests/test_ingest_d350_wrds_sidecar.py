from __future__ import annotations

import pandas as pd
import pytest

from scripts import ingest_d350_wrds_sidecar as mod


def test_normalize_sidecar_builds_schema():
    raw = pd.DataFrame(
        {
            "date": ["2023-11-28", "2023-11-29"],
            "permno": [86544, 86544],
            "price": [25.99, 26.10],
            "total_return": [0.0, -0.02],
            "cusip": ["095229100", "095229100"],
            "ticker": ["AVTA", "AVTA"],
            "company_name": ["Avantax, Inc.", "Avantax, Inc."],
            "issue_date": ["1998-12-15", "1998-12-15"],
            "namedt": ["2023-01-01", "2023-01-01"],
        }
    )

    sidecar = mod._normalize_sidecar(
        raw,
        source_as_of_date=pd.Timestamp("2023-11-29"),
        source_file="wrds:crsp.dsf",
        source_sheet="crsp.dsf",
    )

    assert sidecar.columns.tolist() == mod.SIDECAR_COLUMNS
    assert sidecar["date"].dt.strftime("%Y-%m-%d").tolist() == ["2023-11-28", "2023-11-29"]
    assert sidecar["permno"].tolist() == [86544, 86544]
    assert sidecar["price"].tolist() == [25.99, 26.10]
    assert sidecar["total_return"].tolist() == [0.0, -0.02]
    assert sidecar["source_file"].nunique() == 1
    assert sidecar["source_sheet"].nunique() == 1
    assert pd.Timestamp(sidecar.loc[0, "source_as_of_date"]) == pd.Timestamp("2023-11-29")


def test_normalize_sidecar_blocks_empty_query():
    with pytest.raises(RuntimeError, match="returned no CRSP daily rows"):
        mod._normalize_sidecar(
            pd.DataFrame(),
            source_as_of_date=pd.Timestamp("2023-11-29"),
            source_file="wrds:crsp.dsf",
            source_sheet="crsp.dsf",
        )
