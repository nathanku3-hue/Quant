from __future__ import annotations

import hashlib
import json

import pandas as pd
import pytest

from scripts import pead_d1_sue_builder as d1


def _fundq_row(
    gvkey: str,
    fyearq: int,
    fqtr: int,
    epspxq: float,
    *,
    prccq: float = 25.0,
    cshoq: float = 2.0,
    rdq: str | None = None,
) -> dict[str, object]:
    quarter_end_month = fqtr * 3
    datadate = pd.Timestamp(f"{fyearq}-{quarter_end_month:02d}-28")
    return {
        "gvkey": gvkey,
        "datadate": datadate,
        "rdq": pd.Timestamp(rdq) if rdq else datadate + pd.Timedelta(days=30),
        "fyearq": fyearq,
        "fqtr": fqtr,
        "epspxq": epspxq,
        "ajexq": 10.0,
        "prccq": prccq,
        "cshoq": cshoq,
    }


def _run_d1_core(df: pd.DataFrame) -> pd.DataFrame:
    df = d1.build_quarter_key(df)
    df = d1.compute_adj_eps(df)
    df = d1.deduplicate_fundq(df)
    df = d1.deduplicate_rdq(df)
    df = d1.compute_t4_lag(df)
    df = d1.compute_rolling_std(df)
    df = d1.compute_sue(df)
    return d1.clip_sue_by_rdq(df)


def test_adj_eps_uses_raw_epspxq_without_ajexq_division() -> None:
    df = pd.DataFrame(
        {
            "epspxq": ["2.50", 4.0, None],
            "ajexq": [2.0, 0.5, 3.0],
            "prccq": [20.0, 30.0, 40.0],
            "cshoq": [1.0, 2.0, 3.0],
        }
    )

    out = d1.compute_adj_eps(df)

    assert out["adj_eps"].tolist()[:2] == [2.5, 4.0]
    assert pd.isna(out.loc[2, "adj_eps"])


def test_liquidity_flag_uses_lagged_cshoq_in_compustat_millions() -> None:
    df = pd.DataFrame(
        [
            _fundq_row("LQ", 2020, 1, 1.0, prccq=25.0, cshoq=2.00),
            _fundq_row("LQ", 2020, 2, 1.1, prccq=25.0, cshoq=2.01),
            _fundq_row("LQ", 2020, 3, 1.2, prccq=30.0, cshoq=3.00),
        ]
    )

    out = _run_d1_core(df)
    q2 = out.loc[out["fqtr"].eq(2)].iloc[0]
    q3 = out.loc[out["fqtr"].eq(3)].iloc[0]

    assert q2["cshoq_lag1"] == pytest.approx(2.00)
    assert bool(q2["liquidity_pass"]) is False
    assert q3["cshoq_lag1"] == pytest.approx(2.01)
    assert bool(q3["liquidity_pass"]) is True


def test_t4_lag_requires_exact_four_quarter_continuity() -> None:
    continuous = [
        _fundq_row("OK", 2020, 1, 1.0),
        _fundq_row("OK", 2020, 2, 2.0),
        _fundq_row("OK", 2020, 3, 3.0),
        _fundq_row("OK", 2020, 4, 4.0),
        _fundq_row("OK", 2021, 1, 5.0),
    ]
    gap = [
        _fundq_row("GAP", 2020, 1, 10.0),
        _fundq_row("GAP", 2020, 2, 20.0),
        _fundq_row("GAP", 2020, 3, 30.0),
        _fundq_row("GAP", 2020, 4, 40.0),
        _fundq_row("GAP", 2021, 2, 50.0),
    ]

    out = _run_d1_core(pd.DataFrame(continuous + gap))
    ok_q1 = out.loc[out["gvkey"].eq("OK") & out["fyearq"].eq(2021)].iloc[0]
    gap_q2 = out.loc[out["gvkey"].eq("GAP") & out["fyearq"].eq(2021)].iloc[0]

    assert ok_q1["adj_eps_t4"] == pytest.approx(1.0)
    assert ok_q1["surprise"] == pytest.approx(4.0)
    assert pd.isna(gap_q2["adj_eps_t4"])
    assert bool(gap_q2["valid_sue"]) is False


def test_rdq_dedup_prevents_discarded_quarter_from_creating_t4_lag() -> None:
    shared_rdq = "2020-08-01"
    rows = [
        _fundq_row("DUP", 2020, 1, 1.0, rdq=shared_rdq),
        _fundq_row("DUP", 2020, 2, 2.0, rdq=shared_rdq),
        _fundq_row("DUP", 2020, 3, 3.0),
        _fundq_row("DUP", 2020, 4, 4.0),
        _fundq_row("DUP", 2021, 1, 5.0),
    ]

    out = _run_d1_core(pd.DataFrame(rows))
    target = out.loc[out["fyearq"].eq(2021) & out["fqtr"].eq(1)].iloc[0]

    assert not (out["fyearq"].eq(2020) & out["fqtr"].eq(1)).any()
    assert pd.isna(target["adj_eps_t4"])
    assert bool(target["valid_sue"]) is False


def test_valid_sue_does_not_require_liquidity_pass() -> None:
    rows = [
        _fundq_row("ILLIQ", 2020, 1, 1.0, prccq=25.0, cshoq=2.0),
        _fundq_row("ILLIQ", 2020, 2, 2.0, prccq=25.0, cshoq=2.0),
        _fundq_row("ILLIQ", 2020, 3, 3.0, prccq=25.0, cshoq=2.0),
        _fundq_row("ILLIQ", 2020, 4, 4.0, prccq=25.0, cshoq=2.0),
        _fundq_row("ILLIQ", 2021, 1, 5.0, prccq=25.0, cshoq=2.0),
    ]

    out = _run_d1_core(pd.DataFrame(rows))
    target = out.loc[out["fyearq"].eq(2021) & out["fqtr"].eq(1)].iloc[0]

    assert target["prccq_lag1"] * target["cshoq_lag1"] == pytest.approx(50.0)
    assert bool(target["liquidity_pass"]) is False
    assert bool(target["valid_sue"]) is True


def test_clipped_sue_retains_raw_sue_and_caps_only_extreme_rdq_cross_section() -> None:
    positive_rdq = pd.Timestamp("2021-05-01")
    negative_rdq = pd.Timestamp("2021-05-02")
    single_rdq = pd.Timestamp("2021-05-03")
    zero_std_rdq = pd.Timestamp("2021-05-04")

    rows = (
        [{"rdq": positive_rdq, "sue_price_scaled": 0.0, "label": f"pos-peer-{idx}"} for idx in range(99)]
        + [{"rdq": positive_rdq, "sue_price_scaled": 100.0, "label": "positive-extreme"}]
        + [{"rdq": negative_rdq, "sue_price_scaled": 0.0, "label": f"neg-peer-{idx}"} for idx in range(99)]
        + [{"rdq": negative_rdq, "sue_price_scaled": -100.0, "label": "negative-extreme"}]
        + [{"rdq": single_rdq, "sue_price_scaled": 100.0, "label": "single"}]
        + [{"rdq": zero_std_rdq, "sue_price_scaled": 1.0, "label": f"zero-std-{idx}"} for idx in range(3)]
    )
    df = pd.DataFrame(rows)

    out = d1.clip_sue_by_rdq(df)
    positive_threshold = (
        pd.Series([0.0] * 99 + [100.0]).std() * d1.SUE_CLIP_STD_MULTIPLE
    )
    negative_threshold = (
        pd.Series([0.0] * 99 + [-100.0]).std() * d1.SUE_CLIP_STD_MULTIPLE
    )
    positive = out.loc[out["label"].eq("positive-extreme")].iloc[0]
    negative = out.loc[out["label"].eq("negative-extreme")].iloc[0]

    assert positive["sue_price_scaled"] == pytest.approx(100.0)
    assert positive["sue_price_scaled_clipped"] == pytest.approx(positive_threshold)
    assert negative["sue_price_scaled"] == pytest.approx(-100.0)
    assert negative["sue_price_scaled_clipped"] == pytest.approx(-negative_threshold)
    assert out.loc[out["label"].eq("single"), "sue_price_scaled_clipped"].iloc[0] == pytest.approx(100.0)
    assert out.loc[out["label"].str.startswith("zero-std"), "sue_price_scaled_clipped"].tolist() == [1.0, 1.0, 1.0]


def test_write_output_replaces_tmp_parquet_before_manifest(
    tmp_path, monkeypatch
) -> None:
    out_path = tmp_path / "pead_d1_sue_signal.parquet"
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    real_replace = d1.os.replace
    replace_calls: list[tuple[object, object]] = []

    def _record_replace(source, destination) -> None:
        replace_calls.append((source, destination))
        real_replace(source, destination)

    monkeypatch.setattr(d1.os, "replace", _record_replace)
    df = pd.DataFrame(
        {
            "gvkey": ["W1"],
            "rdq": [pd.Timestamp("2021-05-01")],
            "datadate": [pd.Timestamp("2021-03-31")],
            "fyearq": [2021],
            "fqtr": [1],
            "adj_eps": [2.0],
            "adj_eps_t4": [1.0],
            "surprise": [1.0],
            "prccq_lag1": [25.0],
            "cshoq_lag1": [3.0],
            "liquidity_pass": [True],
            "sue_price_scaled": [0.04],
            "sue_std_scaled": [2.0],
            "sue_price_scaled_clipped": [0.04],
            "n_prior_quarters": [4],
            "valid_sue": [True],
        }
    )

    d1.write_output(df, out_path, manifest_path, dry_run=False)

    assert replace_calls == [
        (d1._tmp_path_for(out_path), out_path),
        (d1._tmp_path_for(manifest_path), manifest_path),
    ]
    assert out_path.exists()
    assert manifest_path.exists()
    assert not d1._tmp_path_for(out_path).exists()
    assert not d1._tmp_path_for(manifest_path).exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sha256"] == hashlib.sha256(out_path.read_bytes()).hexdigest()
    assert "sue_price_scaled_clipped" in manifest["columns"]
    assert manifest["quality_metrics"] == {
        "valid_rows": 1,
        "raw_abs_sue_gt_5_count": 0,
        "raw_abs_sue_gt_5_share": 0.0,
        "clipped_count": 0,
        "clipped_share": 0.0,
        "liquidity_pass_count": 1,
        "liquidity_pass_share": 1.0,
    }
    assert manifest["limitations"] == [d1.CURRENT_VINTAGE_LIMITATION]
    assert "current-vintage" in manifest["limitations"][0]
    assert "restatement hindsight" in manifest["limitations"][0]


def test_quality_summary_reports_valid_row_counts_and_shares() -> None:
    df = pd.DataFrame(
        {
            "valid_sue": [True, True, True, False],
            "sue_price_scaled": [6.0, 1.0, -2.0, 100.0],
            "sue_price_scaled_clipped": [5.0, 1.0, -2.0, 4.0],
            "liquidity_pass": [True, False, True, True],
        }
    )

    summary = d1.summarize_d1_quality(df)

    assert summary == {
        "valid_rows": 3,
        "raw_abs_sue_gt_5_count": 1,
        "raw_abs_sue_gt_5_share": pytest.approx(1 / 3),
        "clipped_count": 1,
        "clipped_share": pytest.approx(1 / 3),
        "liquidity_pass_count": 2,
        "liquidity_pass_share": pytest.approx(2 / 3),
    }


def test_quality_gate_passes_below_threshold_and_fails_at_threshold() -> None:
    below_threshold = {
        "raw_abs_sue_gt_5_share": d1.RAW_ABS_SUE_GT_5_MAX_SHARE - 0.000001
    }
    at_threshold = {
        "raw_abs_sue_gt_5_share": d1.RAW_ABS_SUE_GT_5_MAX_SHARE
    }

    d1.enforce_d1_quality_gate(below_threshold)
    with pytest.raises(RuntimeError, match=r"raw \|SUE\| > 5 share"):
        d1.enforce_d1_quality_gate(at_threshold)


def test_write_output_cleans_partial_parquet_temp_on_failure(
    tmp_path, monkeypatch
) -> None:
    out_path = tmp_path / "pead_d1_sue_signal.parquet"
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    tmp_out_path = d1._tmp_path_for(out_path)
    out_path.write_bytes(b"existing parquet")
    manifest_path.write_bytes(b"existing manifest")
    original_out = (out_path.read_bytes(), out_path.stat().st_mtime_ns)
    original_manifest = (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    )
    df = pd.DataFrame(
        {
            "gvkey": ["FAIL"],
            "rdq": [pd.Timestamp("2021-05-01")],
            "datadate": [pd.Timestamp("2021-03-31")],
            "fyearq": [2021],
            "fqtr": [1],
            "adj_eps": [2.0],
            "adj_eps_t4": [1.0],
            "surprise": [1.0],
            "prccq_lag1": [25.0],
            "cshoq_lag1": [3.0],
            "liquidity_pass": [True],
            "sue_price_scaled": [0.04],
            "sue_std_scaled": [2.0],
            "sue_price_scaled_clipped": [0.04],
            "n_prior_quarters": [4],
            "valid_sue": [True],
        }
    )

    def _fail_after_partial_write(self, path, *, index):
        path.write_bytes(b"partial parquet")
        raise OSError("simulated parquet write failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fail_after_partial_write)

    with pytest.raises(OSError, match="simulated parquet write failure"):
        d1.write_output(df, out_path, manifest_path, dry_run=False)

    assert not tmp_out_path.exists()
    assert not d1._tmp_path_for(manifest_path).exists()
    assert (out_path.read_bytes(), out_path.stat().st_mtime_ns) == original_out
    assert (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    ) == original_manifest


def test_write_output_parquet_replace_failure_does_not_promote_manifest(
    tmp_path, monkeypatch
) -> None:
    out_path = tmp_path / "pead_d1_sue_signal.parquet"
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    out_path.write_bytes(b"existing parquet")
    manifest_path.write_bytes(b"existing manifest")
    original_out = (out_path.read_bytes(), out_path.stat().st_mtime_ns)
    original_manifest = (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    )
    replace_calls: list[tuple[object, object]] = []

    def _fail_parquet_replace(source, destination) -> None:
        replace_calls.append((source, destination))
        raise OSError("simulated parquet replace failure")

    monkeypatch.setattr(d1.os, "replace", _fail_parquet_replace)
    df = pd.DataFrame(
        {
            "gvkey": ["FAIL"],
            "rdq": [pd.Timestamp("2021-05-01")],
            "datadate": [pd.Timestamp("2021-03-31")],
            "fyearq": [2021],
            "fqtr": [1],
            "adj_eps": [2.0],
            "adj_eps_t4": [1.0],
            "surprise": [1.0],
            "prccq_lag1": [25.0],
            "cshoq_lag1": [3.0],
            "liquidity_pass": [True],
            "sue_price_scaled": [0.04],
            "sue_std_scaled": [2.0],
            "sue_price_scaled_clipped": [0.04],
            "n_prior_quarters": [4],
            "valid_sue": [True],
        }
    )

    with pytest.raises(OSError, match="simulated parquet replace failure"):
        d1.write_output(df, out_path, manifest_path, dry_run=False)

    assert replace_calls == [(d1._tmp_path_for(out_path), out_path)]
    assert not d1._tmp_path_for(out_path).exists()
    assert not d1._tmp_path_for(manifest_path).exists()
    assert (out_path.read_bytes(), out_path.stat().st_mtime_ns) == original_out
    assert (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    ) == original_manifest


@pytest.mark.parametrize("dry_run", [False, True])
def test_main_empty_result_exits_without_touching_existing_outputs(
    tmp_path, monkeypatch, dry_run
) -> None:
    input_path = tmp_path / "comp_fundq.parquet"
    input_path.write_bytes(b"input placeholder")
    out_path = tmp_path / "pead_d1_sue_signal.parquet"
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    out_path.write_bytes(b"existing parquet")
    manifest_path.write_bytes(b"existing manifest")
    original_out = (out_path.read_bytes(), out_path.stat().st_mtime_ns)
    original_manifest = (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    )
    empty_fundq = pd.DataFrame(
        columns=[
            "gvkey", "datadate", "rdq", "fyearq", "fqtr",
            "epspxq", "prccq", "cshoq",
        ]
    )

    monkeypatch.setattr(d1, "FUNDQ_PATH", input_path)
    monkeypatch.setattr(d1, "OUT_PATH", out_path)
    monkeypatch.setattr(d1, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        d1,
        "load_fundq",
        lambda path, start_date: empty_fundq.copy(),
    )
    argv = ["pead_d1_sue_builder.py", "--start-date", "2099-01-01"]
    if dry_run:
        argv.append("--dry-run")
    monkeypatch.setattr(d1.sys, "argv", argv)

    with pytest.raises(SystemExit) as exc_info:
        d1.main()

    assert exc_info.value.code != 0
    assert "No processed D1 SUE rows remain" in str(exc_info.value)
    assert "existing outputs were not touched" in str(exc_info.value)
    assert (out_path.read_bytes(), out_path.stat().st_mtime_ns) == original_out
    assert (
        manifest_path.read_bytes(),
        manifest_path.stat().st_mtime_ns,
    ) == original_manifest
    assert not d1._tmp_path_for(out_path).exists()
    assert not d1._tmp_path_for(manifest_path).exists()


def test_write_output_cleans_manifest_temp_when_replace_fails(
    tmp_path, monkeypatch
) -> None:
    out_path = tmp_path / "pead_d1_sue_signal.parquet"
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    tmp_manifest_path = d1._tmp_path_for(manifest_path)
    df = pd.DataFrame(
        {
            "gvkey": ["FAIL-MANIFEST"],
            "rdq": [pd.Timestamp("2021-05-01")],
            "datadate": [pd.Timestamp("2021-03-31")],
            "fyearq": [2021],
            "fqtr": [1],
            "adj_eps": [2.0],
            "adj_eps_t4": [1.0],
            "surprise": [1.0],
            "prccq_lag1": [25.0],
            "cshoq_lag1": [3.0],
            "liquidity_pass": [True],
            "sue_price_scaled": [0.04],
            "sue_std_scaled": [2.0],
            "sue_price_scaled_clipped": [0.04],
            "n_prior_quarters": [4],
            "valid_sue": [True],
        }
    )
    real_replace = d1.os.replace

    def _fail_manifest_replace(src, dst):
        if dst == manifest_path:
            raise OSError("simulated manifest replace failure")
        real_replace(src, dst)

    monkeypatch.setattr(d1.os, "replace", _fail_manifest_replace)

    with pytest.raises(OSError, match="simulated manifest replace failure"):
        d1.write_output(df, out_path, manifest_path, dry_run=False)

    assert out_path.exists()
    assert not manifest_path.exists()
    assert not d1._tmp_path_for(out_path).exists()
    assert not tmp_manifest_path.exists()
