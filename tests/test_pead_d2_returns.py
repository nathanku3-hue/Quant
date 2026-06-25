from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import pead_d2_return_contract as contract


def _raw(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "prccd": 100.0,
        "trfd": 1.0,
        "ajexdi": 1.0,
        "cshtrd": 10.0,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def _source(
    rows: list[dict[str, object]],
    name: str = "comp_secd_2015_2019",
) -> pd.DataFrame:
    return contract._prepare_source_frame(_raw(rows), name)


def _empty_source() -> pd.DataFrame:
    return pd.DataFrame(columns=contract.STANDARDIZED_COLUMNS)


def _build(rows: list[dict[str, object]]) -> pd.DataFrame:
    return contract.build_security_returns(_source(rows), _empty_source())


def test_total_return_level_formula_identity_and_changed_levels_are_nonzero() -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0, "trfd": 1.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 100.0, "trfd": 1.02},
            {"gvkey": "001", "iid": "01", "date": "2020-01-06", "prccd": 105.0, "trfd": 1.02},
        ]
    )

    assert output["tr_level"].tolist() == pytest.approx([100.0, 102.0, 107.1])
    assert np.isnan(output.loc[0, "total_return"])
    assert output.loc[1, "total_return"] == pytest.approx(0.02)
    assert output.loc[2, "total_return"] == pytest.approx(0.05)
    assert output.loc[1:, "return_type"].tolist() == ["total_return", "total_return"]

    quality = contract._return_quality_metrics(output)
    assert quality["changed_valid_tr_level_count"] == 2
    assert quality["changed_valid_tr_level_nonzero_return_pct"] > 0.99


def test_dividend_total_return_differs_from_price_fallback() -> None:
    output = _build(
        [
            {"gvkey": "TOTAL", "iid": "01", "date": "2020-01-02", "prccd": 100.0, "trfd": 1.0},
            {"gvkey": "TOTAL", "iid": "01", "date": "2020-01-03", "prccd": 99.0, "trfd": 1.02},
            {"gvkey": "PRICE", "iid": "01", "date": "2020-01-02", "prccd": 100.0, "trfd": np.nan},
            {"gvkey": "PRICE", "iid": "01", "date": "2020-01-03", "prccd": 99.0, "trfd": np.nan},
        ]
    )

    total = output.query("gvkey == 'TOTAL'").iloc[1]
    fallback = output.query("gvkey == 'PRICE'").iloc[1]
    assert total["return_type"] == "total_return"
    assert total["total_return"] == pytest.approx((99.0 * 1.02) / 100.0 - 1.0)
    assert fallback["return_type"] == "price_return_fallback"
    assert fallback["total_return"] == pytest.approx(-0.01)
    assert total["total_return"] != pytest.approx(fallback["total_return"])


def test_missing_either_tr_level_uses_same_security_price_fallback() -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0, "trfd": 1.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 102.0, "trfd": np.nan},
            {"gvkey": "001", "iid": "01", "date": "2020-01-06", "prccd": 103.0, "trfd": 1.0},
        ]
    )

    assert output.loc[1, "return_type"] == "price_return_fallback"
    assert output.loc[1, "total_return"] == pytest.approx(0.02)
    assert output.loc[2, "return_type"] == "price_return_fallback"
    assert output.loc[2, "total_return"] == pytest.approx(103.0 / 102.0 - 1.0)


def test_lags_never_cross_iid_and_every_series_is_preserved() -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-03", "prccd": 200.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-06", "prccd": 202.0},
        ]
    )

    assert set(output["security_id"]) == {"001-01", "001-02"}
    first_by_security = output.groupby("security_id", sort=False).head(1)
    assert first_by_security["total_return"].isna().all()
    second = output.groupby("security_id", sort=False).nth(1).set_index("security_id")
    assert second.loc["001-01", "total_return"] == pytest.approx(0.01)
    assert second.loc["001-02", "total_return"] == pytest.approx(0.01)


def test_gap_and_extreme_return_guardrails_are_grouped_by_security() -> None:
    output = _build(
        [
            {"gvkey": "GAP", "iid": "01", "date": "2020-01-01", "prccd": 100.0},
            {"gvkey": "GAP", "iid": "01", "date": "2020-01-10", "prccd": 101.0},
            {"gvkey": "EXTREME", "iid": "02", "date": "2020-01-01", "prccd": 100.0},
            {"gvkey": "EXTREME", "iid": "02", "date": "2020-01-02", "prccd": 700.0},
        ]
    )

    gap = output.query("gvkey == 'GAP'").iloc[1]
    extreme = output.query("gvkey == 'EXTREME'").iloc[1]
    assert np.isnan(gap["total_return"])
    assert gap["guardrail_reason"] == "date_gap_gt_5"
    assert np.isnan(extreme["total_return"])
    assert extreme["guardrail_reason"] == "abs_return_gt_5"


def test_daily_source_wins_only_exact_source_overlap() -> None:
    secd = _source(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-02", "prccd": 300.0},
        ]
    )
    daily = _source(
        [{"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 200.0}],
        "prices_daily_compustat",
    )

    output = contract.merge_and_validate(secd, daily)
    assert len(output) == 2
    overlapped = output.query("iid == '01'").iloc[0]
    untouched = output.query("iid == '02'").iloc[0]
    assert overlapped["price_level"] == pytest.approx(200.0)
    assert overlapped["data_source"] == "prices_daily_compustat"
    assert untouched["price_level"] == pytest.approx(300.0)
    assert untouched["data_source"] == "comp_secd_2015_2019"


def test_duplicate_source_keys_fail_closed_after_normalization() -> None:
    duplicate = _raw(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": " 001 ", "iid": "01", "date": "2020-01-02"},
        ]
    )
    with pytest.raises(ValueError, match="duplicate .* source keys"):
        contract._prepare_source_frame(duplicate, "comp_secd_2015_2019")


def test_duplicate_security_id_date_collision_fails_closed() -> None:
    source = _source(
        [
            {"gvkey": "A-B", "iid": "C", "date": "2020-01-02"},
            {"gvkey": "A", "iid": "B-C", "date": "2020-01-02"},
        ]
    )
    with pytest.raises(ValueError, match="one-to-one"):
        contract.merge_and_validate(source, _empty_source())


def test_security_id_date_is_unique_and_dollar_volume_is_not_adv() -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 10.0, "cshtrd": 25.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-02", "prccd": 20.0, "cshtrd": 30.0},
        ]
    )
    assert not output.duplicated(["security_id", "date"]).any()
    assert "adv" not in output.columns
    assert output.set_index("security_id").loc["001-01", "dollar_volume"] == pytest.approx(250.0)


def test_event_window_flag_is_rejected_with_explicit_d2b_message(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        contract.main(["--event-window-only"])
    assert excinfo.value.code == 2
    error = capsys.readouterr().err
    assert "disabled in D2A" in error
    assert "D2B" in error
    assert "+60 market sessions" in error


def test_full_build_flag_routes_to_bounded_builder(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secd_path = tmp_path / "secd.parquet"
    daily_path = tmp_path / "daily.parquet"
    manifest_path = tmp_path / "returns.parquet.manifest.json"
    secd_path.touch()
    daily_path.touch()
    monkeypatch.setattr(contract, "SECD_PATH", secd_path)
    monkeypatch.setattr(contract, "DAILY_PATH", daily_path)
    called = 0

    def fake_full_build() -> Path:
        nonlocal called
        called += 1
        manifest_path.write_text(
            json.dumps(
                {
                    "parquet_file": "returns.abc.parquet",
                    "row_count": 10,
                    "security_count": 2,
                }
            ),
            encoding="utf-8",
        )
        return manifest_path

    monkeypatch.setattr(contract, "build_full_contract", fake_full_build)
    monkeypatch.setattr(
        contract,
        "process_secd",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("sample path must not run")
        ),
    )
    contract.main(["--build"])
    assert called == 1
    assert "rows=10" in capsys.readouterr().out


def test_under_500_sample_fails_before_source_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secd_path = tmp_path / "secd.parquet"
    daily_path = tmp_path / "daily.parquet"
    secd_path.touch()
    daily_path.touch()
    monkeypatch.setattr(contract, "SECD_PATH", secd_path)
    monkeypatch.setattr(contract, "DAILY_PATH", daily_path)
    monkeypatch.setattr(
        contract, "_sample_gvkeys", lambda _path, _size: [str(i) for i in range(499)]
    )

    def unexpected_process(*_args: object, **_kwargs: object) -> pd.DataFrame:
        raise AssertionError("source processing must not run for an under-500 sample")

    monkeypatch.setattr(contract, "process_secd", unexpected_process)
    with pytest.raises(SystemExit, match="requires exactly 500 GVKEYs; found 499"):
        contract.main([])


def test_manifest_hash_formula_security_counts_and_utf8_publication(tmp_path: Path) -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-02", "prccd": 200.0},
        ]
    )
    out_path = tmp_path / "returns.parquet"
    manifest_path = contract.publish_contract(output, out_path, "synthetic")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_path = manifest_path.parent / manifest["parquet_file"]
    assert not out_path.exists()
    assert versioned_path.exists()
    assert manifest["sha256"] == hashlib.sha256(versioned_path.read_bytes()).hexdigest()
    assert manifest["security_count"] == 2
    assert manifest["unique_security_id_date"] is True
    assert manifest["methodology"]["total_return_level"] == "TR_level = prccd * trfd / ajexdi"
    assert "trfd_t / trfd_{t-1} - 1" in manifest["methodology"]["supersedes"]
    assert manifest["return_quality"]["formula_identity_max_abs_error"] == 0.0
    assert manifest["publication"]["commit_point"] == manifest_path.name
    assert not list(tmp_path.glob("*.tmp"))


def test_formula_quality_metric_is_measured_not_hardcoded() -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
        ]
    )
    perturbed = output.copy()
    perturbed.loc[1, "total_return"] += 0.001
    quality = contract._return_quality_metrics(perturbed)
    assert quality["formula_identity_max_abs_error"] == pytest.approx(0.001)


def test_publication_failure_cleans_temps_without_creating_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
        ]
    )
    out_path = tmp_path / "returns.parquet"

    def fail_to_parquet(self: pd.DataFrame, path: Path, **kwargs: object) -> None:
        Path(path).write_bytes(b"partial")
        raise RuntimeError("synthetic parquet failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail_to_parquet)
    with pytest.raises(RuntimeError, match="synthetic parquet failure"):
        contract.publish_contract(output, out_path, "synthetic")
    assert not out_path.exists()
    assert not out_path.with_suffix(".parquet.manifest.json").exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_manifest_replace_interruption_keeps_old_commit_pointer_and_cleans_new_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
        ]
    )
    out_path = tmp_path / "returns.parquet"
    manifest_path = contract.publish_contract(old_output, out_path, "old")
    old_manifest_bytes = manifest_path.read_bytes()
    old_manifest = json.loads(old_manifest_bytes.decode("utf-8"))
    old_versioned_path = manifest_path.parent / old_manifest["parquet_file"]
    old_versioned_bytes = old_versioned_path.read_bytes()

    new_output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 102.0},
        ]
    )
    real_replace = os.replace

    def fail_new_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise OSError("synthetic manifest replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", fail_new_manifest_replace)
    with pytest.raises(OSError, match="synthetic manifest replace failure"):
        contract.publish_contract(new_output, out_path, "new")

    assert manifest_path.read_bytes() == old_manifest_bytes
    assert old_versioned_path.read_bytes() == old_versioned_bytes
    assert hashlib.sha256(old_versioned_bytes).hexdigest() == old_manifest["sha256"]
    assert len(list(tmp_path.glob("returns.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))


def test_publication_lock_rejects_concurrent_writer(tmp_path: Path) -> None:
    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
        ]
    )
    out_path = tmp_path / "returns.parquet"
    lock_path = out_path.with_suffix(".parquet.lock")
    with contract._publication_lock(lock_path):
        with pytest.raises(RuntimeError, match="publication lock is already held"):
            contract.publish_contract(output, out_path, "synthetic")


def test_security_id_must_map_one_to_one_with_gvkey_iid() -> None:
    with pytest.raises(ValueError, match="one-to-one"):
        _build(
            [
                {"gvkey": "a-b", "iid": "c", "date": "2020-01-02"},
                {"gvkey": "a", "iid": "b-c", "date": "2020-01-03"},
            ]
        )


def test_empty_data_invalid_identity_and_empty_output_path_fail_before_write(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        contract.merge_and_validate(_empty_source(), _empty_source())

    output = _build(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02"},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
        ]
    )
    invalid = output.copy()
    invalid.loc[0, "security_id"] = "wrong"
    with pytest.raises(ValueError, match="security_id identity"):
        contract.publish_contract(invalid, tmp_path / "invalid.parquet", "synthetic")
    with pytest.raises(ValueError, match="non-empty .parquet"):
        contract.publish_contract(output, Path(), "synthetic")
    assert not list(tmp_path.iterdir())


def _full_source_fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    secd = _raw(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-02", "prccd": 100.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.0},
            {"gvkey": "001", "iid": "01", "date": "2020-01-06", "prccd": 102.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-02", "prccd": 200.0},
            {"gvkey": "001", "iid": "02", "date": "2020-01-03", "prccd": 202.0},
            {"gvkey": "002", "iid": "01", "date": "2020-01-02", "prccd": 50.0},
            {"gvkey": "002", "iid": "01", "date": "2020-01-03", "prccd": 51.0},
        ]
    )
    daily = _raw(
        [
            {"gvkey": "001", "iid": "01", "date": "2020-01-03", "prccd": 101.5},
            {"gvkey": "002", "iid": "01", "date": "2020-01-06", "prccd": 52.0},
        ]
    )
    return secd, daily


def test_full_build_is_bounded_and_semantically_equivalent(tmp_path: Path) -> None:
    secd_raw, daily_raw = _full_source_fixtures()
    secd_path = tmp_path / "secd.parquet"
    daily_path = tmp_path / "daily.parquet"
    out_path = tmp_path / "returns.parquet"
    secd_raw.to_parquet(secd_path, index=False)
    daily_raw.to_parquet(daily_path, index=False)
    expected = contract.build_security_returns(
        contract._prepare_source_frame(secd_raw, "comp_secd_2015_2019"),
        contract._prepare_source_frame(daily_raw, "prices_daily_compustat"),
    )

    with pytest.MonkeyPatch.context() as bounded:
        bounded.setattr(
            pd,
            "read_parquet",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full build must not materialize a source frame")
            ),
        )
        bounded.setattr(
            pd.DataFrame,
            "to_parquet",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full build must not materialize the output frame")
            ),
        )
        manifest_path = contract.build_full_contract(
            secd_path, daily_path, out_path, "fixture_full"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_path = manifest_path.parent / manifest["parquet_file"]
    actual = pd.read_parquet(versioned_path)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
    assert not out_path.exists()
    assert manifest["sha256"] == contract._sha256_file(versioned_path)
    assert manifest["row_count"] == len(expected)
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_full_build_duplicate_source_fails_closed_without_publication(tmp_path: Path) -> None:
    secd_raw, daily_raw = _full_source_fixtures()
    duplicate = pd.concat([secd_raw, secd_raw.iloc[[0]]], ignore_index=True)
    secd_path = tmp_path / "secd.parquet"
    daily_path = tmp_path / "daily.parquet"
    out_path = tmp_path / "returns.parquet"
    duplicate.to_parquet(secd_path, index=False)
    daily_raw.to_parquet(daily_path, index=False)

    with pytest.raises(ValueError, match="duplicate .* source keys"):
        contract.build_full_contract(secd_path, daily_path, out_path)
    assert not out_path.with_suffix(".parquet.manifest.json").exists()
    assert not list(tmp_path.glob("returns.*.parquet"))
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_full_build_manifest_interruption_preserves_old_pointer_and_cleans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secd_raw, daily_raw = _full_source_fixtures()
    secd_path = tmp_path / "secd.parquet"
    daily_path = tmp_path / "daily.parquet"
    out_path = tmp_path / "returns.parquet"
    secd_raw.to_parquet(secd_path, index=False)
    daily_raw.to_parquet(daily_path, index=False)
    manifest_path = contract.build_full_contract(secd_path, daily_path, out_path, "old")
    old_manifest = manifest_path.read_bytes()
    changed = daily_raw.copy()
    changed.loc[0, "prccd"] = 103.0
    changed.to_parquet(daily_path, index=False)
    real_replace = os.replace

    def fail_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise OSError("synthetic full-build manifest interruption")
        real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="synthetic full-build manifest interruption"):
        contract.build_full_contract(secd_path, daily_path, out_path, "new")

    assert manifest_path.read_bytes() == old_manifest
    assert len(list(tmp_path.glob("returns.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))
