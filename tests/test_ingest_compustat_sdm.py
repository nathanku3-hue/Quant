from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts import ingest_compustat_sdm as sdm


def test_select_totalq_columns_prefers_required_then_optional() -> None:
    available = {
        "gvkey",
        "datadate",
        "k_int",
        "q_tot",
        "k_phy",
        "ik_tot",
        "random_col",
    }
    cols = sdm._select_totalq_columns(available)
    assert cols[:2] == ["gvkey", "datadate"]
    assert "k_int" in cols
    assert "q_tot" in cols
    assert "k_phy" in cols
    assert "ik_tot" in cols
    assert "random_col" not in cols


def test_assert_merge_asof_sorted_raises_on_unsorted() -> None:
    df = pd.DataFrame(
        {
            "published_at_dt": [
                pd.Timestamp("2024-01-03"),
                pd.Timestamp("2024-01-01"),
            ]
        }
    )
    try:
        sdm._assert_merge_asof_sorted(df, "published_at_dt", "left")
        assert False, "Expected ValueError for unsorted asof key."
    except ValueError as exc:
        assert "globally sorted" in str(exc)


def test_join_totalq_merges_after_global_key_sort() -> None:
    df_fundq = pd.DataFrame(
        {
            "gvkey": ["A", "A", "B", "B"],
            "published_at": [
                pd.Timestamp("2024-01-15", tz="UTC"),
                pd.Timestamp("2024-03-15", tz="UTC"),
                pd.Timestamp("2024-02-01", tz="UTC"),
                pd.Timestamp("2024-04-01", tz="UTC"),
            ],
            "ppentq": [10.0, 10.0, 20.0, 20.0],
        }
    )
    df_tq = pd.DataFrame(
        {
            "gvkey": ["A", "B"],
            "datadate": [pd.Timestamp("2023-08-31"), pd.Timestamp("2023-08-31")],
            "k_int": [30.0, 40.0],
            "q_tot": [1.2, 0.9],
        }
    )

    out = sdm._join_totalq(df_fundq, df_tq)
    assert len(out) == len(df_fundq)
    assert out["k_int"].notna().sum() == 4
    assert "intang_intensity" in out.columns
    assert "invest_disc" in out.columns
    assert "q_regime" in out.columns


def test_crosswalk_permno_allow_and_audit(tmp_path: Path) -> None:
    sector_map_path = tmp_path / "sector_map.parquet"
    audit_path = tmp_path / "audit.csv"

    pd.DataFrame(
        {
            "ticker": ["NVDA"],
            "permno": [12345],
        }
    ).to_parquet(sector_map_path, index=False)

    df = pd.DataFrame(
        {
            "gvkey": ["001", "002"],
            "ticker": ["NVDA", "UNMAPPED"],
            "fiscal_date": [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-01-31")],
            "published_at": [
                pd.Timestamp("2024-02-20", tz="UTC"),
                pd.Timestamp("2024-02-20", tz="UTC"),
            ],
        }
    )

    out = sdm._crosswalk_permno(df, sm_path=sector_map_path, audit_path=audit_path)
    assert len(out) == 2
    assert out["permno"].notna().sum() == 1
    assert audit_path.exists()
    audit = pd.read_csv(audit_path)
    assert "UNMAPPED" in set(audit["ticker"])


def test_crosswalk_permno_dry_run_skips_audit_write(tmp_path: Path) -> None:
    sector_map_path = tmp_path / "sector_map.parquet"
    audit_path = tmp_path / "audit.csv"
    pd.DataFrame({"ticker": ["NVDA"], "permno": [12345]}).to_parquet(sector_map_path, index=False)

    df = pd.DataFrame(
        {
            "gvkey": ["001"],
            "ticker": ["UNMAPPED"],
            "fiscal_date": [pd.Timestamp("2024-01-31")],
            "published_at": [pd.Timestamp("2024-02-20", tz="UTC")],
        }
    )

    out = sdm._crosswalk_permno(
        df,
        sm_path=sector_map_path,
        audit_path=audit_path,
        write_audit=False,
    )
    assert len(out) == 1
    assert out["permno"].isna().all()
    assert not audit_path.exists()
