from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts import assemble_sdm_features as asm


def _write_inputs(base: Path) -> tuple[Path, Path, Path, Path]:
    fundamentals_path = base / "fundamentals_sdm.parquet"
    macro_path = base / "macro_rates.parquet"
    ff_path = base / "ff_factors.parquet"
    sector_map_path = base / "sector_map.parquet"

    pd.DataFrame(
        {
            "gvkey": ["001", "002"],
            "ticker": ["NVDA", "MISS"],
            "permno": [11111, pd.NA],
            "published_at": [
                pd.Timestamp("2024-01-03 12:00:00", tz="UTC"),
                pd.Timestamp("2024-01-05 12:00:00", tz="UTC"),
            ],
            "rev_accel": [0.1, 0.2],
            "op_lev": [0.01, 0.02],
        }
    ).to_parquet(fundamentals_path, index=False)

    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-04")],
            "yield_slope_10y2y": [0.11, 0.22],
            "credit_spread_hy": [3.1, 3.2],
        }
    ).to_parquet(macro_path, index=False)

    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-04")],
            "mktrf": [0.01, 0.02],
            "smb": [0.001, 0.002],
            "hml": [0.003, 0.004],
            "rmw": [0.005, 0.006],
            "cma": [0.007, 0.008],
            "umd": [0.009, 0.010],
        }
    ).to_parquet(ff_path, index=False)

    pd.DataFrame(
        {
            "permno": [11111],
            "ticker": ["MISS"],
            "sector": ["Technology"],
            "industry": ["Semiconductors"],
        }
    ).to_parquet(sector_map_path, index=False)

    return fundamentals_path, macro_path, ff_path, sector_map_path


def test_assemble_features_merges_asof_and_context(tmp_path: Path) -> None:
    fundamentals_path, macro_path, ff_path, sector_map_path = _write_inputs(tmp_path)
    out = asm.assemble_features(
        fundamentals_path=fundamentals_path,
        macro_path=macro_path,
        ff_path=ff_path,
        sector_map_path=sector_map_path,
    )

    # Daily expansion from quarterly snapshots:
    # gvkey=001 starts at 2024-01-03 -> rows on 03/04/05
    # gvkey=002 starts at 2024-01-05 -> row on 05
    assert len(out) == 4
    assert "date" in out.columns
    assert out["date"].nunique() >= 3

    jan3 = out[(out["gvkey"] == "001") & (out["date"] == pd.Timestamp("2024-01-03"))].iloc[0]
    jan4 = out[(out["gvkey"] == "001") & (out["date"] == pd.Timestamp("2024-01-04"))].iloc[0]
    jan5 = out[(out["gvkey"] == "001") & (out["date"] == pd.Timestamp("2024-01-05"))].iloc[0]
    miss = out[(out["gvkey"] == "002") & (out["date"] == pd.Timestamp("2024-01-05"))].iloc[0]

    # Macro/FF asof mapping on daily timeline.
    assert jan3["yield_slope_10y2y"] == 0.11
    assert jan4["yield_slope_10y2y"] == 0.22
    assert jan5["yield_slope_10y2y"] == 0.22
    assert jan3["mktrf"] == 0.01
    assert jan4["mktrf"] == 0.02
    assert jan5["mktrf"] == 0.02

    # SDM ffill persists prior quarterly values into intermediate days.
    assert jan4["rev_accel"] == jan3["rev_accel"]
    assert jan4["op_lev"] == jan3["op_lev"]

    # Context: first by permno, missing-permno row by ticker fallback.
    assert jan3["sector"] == "Technology"
    assert miss["industry"] == "Semiconductors"

    # Method B precomputes.
    assert "ind_rev_accel" in out.columns
    assert "CycleSetup" in out.columns


def test_assemble_features_respects_tolerance_window(tmp_path: Path) -> None:
    fundamentals_path = tmp_path / "fundamentals_sdm.parquet"
    macro_path = tmp_path / "macro_rates.parquet"
    ff_path = tmp_path / "ff_factors.parquet"
    sector_map_path = tmp_path / "sector_map.parquet"

    pd.DataFrame(
        {
            "gvkey": ["001"],
            "ticker": ["NVDA"],
            "published_at": [pd.Timestamp("2024-02-15 00:00:00", tz="UTC")],
        }
    ).to_parquet(fundamentals_path, index=False)

    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-01")],
            "yield_slope_10y2y": [0.11],
        }
    ).to_parquet(macro_path, index=False)

    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-01")],
            "mktrf": [0.01],
            "smb": [0.001],
            "hml": [0.002],
            "rmw": [0.003],
            "cma": [0.004],
            "umd": [0.005],
        }
    ).to_parquet(ff_path, index=False)

    pd.DataFrame({"ticker": ["NVDA"], "sector": ["Technology"], "industry": ["Semis"]}).to_parquet(
        sector_map_path,
        index=False,
    )

    out = asm.assemble_features(
        fundamentals_path=fundamentals_path,
        macro_path=macro_path,
        ff_path=ff_path,
        sector_map_path=sector_map_path,
    )
    assert out["yield_slope_10y2y"].isna().all()
    assert out["mktrf"].isna().all()


def test_assemble_features_requires_full_ff_factor_columns(tmp_path: Path) -> None:
    fundamentals_path = tmp_path / "fundamentals_sdm.parquet"
    macro_path = tmp_path / "macro_rates.parquet"
    ff_path = tmp_path / "ff_factors.parquet"
    sector_map_path = tmp_path / "sector_map.parquet"

    pd.DataFrame(
        {
            "gvkey": ["001"],
            "ticker": ["NVDA"],
            "published_at": [pd.Timestamp("2024-01-10 00:00:00", tz="UTC")],
        }
    ).to_parquet(fundamentals_path, index=False)
    pd.DataFrame({"date": [pd.Timestamp("2024-01-01")], "yield_slope_10y2y": [0.1]}).to_parquet(
        macro_path,
        index=False,
    )
    # Missing smb/hml/rmw/cma/umd by design.
    pd.DataFrame({"date": [pd.Timestamp("2024-01-01")], "mktrf": [0.01]}).to_parquet(ff_path, index=False)
    pd.DataFrame({"ticker": ["NVDA"], "sector": ["Technology"], "industry": ["Semis"]}).to_parquet(
        sector_map_path,
        index=False,
    )

    try:
        asm.assemble_features(
            fundamentals_path=fundamentals_path,
            macro_path=macro_path,
            ff_path=ff_path,
            sector_map_path=sector_map_path,
        )
        assert False, "Expected ValueError when ff factor columns are missing."
    except ValueError as exc:
        assert "ff_factors missing required columns" in str(exc)


def test_assemble_features_cyclesetup_formula(tmp_path: Path) -> None:
    fundamentals_path, macro_path, ff_path, sector_map_path = _write_inputs(tmp_path)
    out = asm.assemble_features(
        fundamentals_path=fundamentals_path,
        macro_path=macro_path,
        ff_path=ff_path,
        sector_map_path=sector_map_path,
    )
    row = out[out["date"] == pd.Timestamp("2024-01-04")].iloc[0]
    expected = float(row["yield_slope_10y2y"]) * float(row["rmw"]) * float(row["cma"])
    assert abs(float(row["CycleSetup"]) - expected) <= 1e-12
    assert abs(float(row["cycle_setup"]) - expected) <= 1e-12


def test_count_rows_nulled_by_tolerance_detects_stale_matches() -> None:
    left = pd.Series(
        [
            pd.Timestamp("2024-01-10 00:00:00", tz="UTC"),
            pd.Timestamp("2024-02-01 00:00:00", tz="UTC"),
        ]
    )
    right = pd.Series([pd.Timestamp("2024-01-01 00:00:00")])
    out = asm._count_rows_nulled_by_tolerance(
        left_keys=left,
        right_keys=right,
        tolerance=pd.Timedelta("14d"),
    )
    assert out["nulled_by_tolerance"] == 1
    assert out["no_prior_match"] == 0
    assert out["matched_with_tolerance"] == 1
