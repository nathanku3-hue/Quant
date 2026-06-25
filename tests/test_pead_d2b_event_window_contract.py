from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import pead_d2b_event_window_contract as contract


def _d1(events: list[tuple[str, object, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gvkey": issuer,
                "rdq": event_date,
                "valid_sue": True,
                "sue_price_scaled": sue,
                "sue_price_scaled_clipped": sue,
            }
            for issuer, event_date, sue in events
        ]
    )


def _row(
    issuer: str,
    iid: str,
    date: object,
    *,
    volume: float | None = 100.0,
    asset_return: float | None = 0.01,
) -> dict[str, object]:
    return {
        "gvkey": issuer,
        "iid": iid,
        "security_id": f"{issuer}-{iid}",
        "date": date,
        "total_return": asset_return,
        "return_type": "total_return" if asset_return is not None else "unavailable",
        "dollar_volume": volume,
        "data_source": "synthetic",
        "tr_level": 100.0,
        "price_level": 100.0,
        "guardrail_reason": "",
    }


def _security_rows(
    issuer: str,
    iid: str,
    sessions: pd.DatetimeIndex,
    volumes: float | list[float] = 100.0,
    returns: float | list[float | None] = 0.01,
) -> list[dict[str, object]]:
    volume_values = [volumes] * len(sessions) if np.isscalar(volumes) else list(volumes)
    return_values = [returns] * len(sessions) if np.isscalar(returns) else list(returns)
    return [
        _row(issuer, iid, date, volume=volume, asset_return=asset_return)
        for date, volume, asset_return in zip(
            sessions, volume_values, return_values, strict=True
        )
    ]


def _standard_contract(
    *,
    event_date: object | None = None,
    sessions: pd.DatetimeIndex | None = None,
) -> tuple[pd.DataFrame, pd.DatetimeIndex, pd.DataFrame, pd.DataFrame]:
    market = sessions if sessions is not None else pd.bdate_range("2024-01-02", periods=100)
    event = event_date if event_date is not None else market[30]
    d1 = _d1([("001", event, 1.25)])
    rows = [
        *_security_rows("001", "01", market, 200.0),
        *_security_rows("001", "02", market, 100.0),
    ]
    d2a = pd.DataFrame(rows, columns=contract.D2A_COLUMNS)
    return contract.build_event_window_contract(d1, d2a), market, d1, d2a


def _provenance() -> dict[str, dict[str, object]]:
    return {
        "d1": {"parquet_path": "d1.parquet", "parquet_sha256": "1" * 64},
        "d2a": {"parquet_path": "d2a.parquet", "parquet_sha256": "2" * 64},
    }


def test_pit_cutoff_excludes_event_day_and_future_liquidity() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    event_date = sessions[30]
    volume_01 = [200.0] * 30 + [1.0] * 70
    volume_02 = [100.0] * 30 + [100_000.0] * 70
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, volume_01),
            *_security_rows("001", "02", sessions, volume_02),
        ]
    )

    output = contract.build_event_window_contract(_d1([("001", event_date, 1.0)]), d2a)

    assert output["security_id"].drop_duplicates().tolist() == ["001-01"]
    assert output["selection_cutoff_date"].iloc[0] == sessions[29]
    assert output["liquidity_observations"].iloc[0] == 20
    assert output["trailing_mean_dollar_volume"].iloc[0] == pytest.approx(200.0)


def test_selection_is_fixed_despite_post_event_daily_leadership_changes() -> None:
    output, sessions, _, d2a = _standard_contract()
    event_date = sessions[30]
    d2a.loc[
        d2a["security_id"].eq("001-02") & pd.to_datetime(d2a["date"]).gt(event_date),
        "dollar_volume",
    ] = 1_000_000.0

    rebuilt = contract.build_event_window_contract(_d1([("001", event_date, 1.0)]), d2a)

    assert rebuilt["security_id"].eq("001-01").all()
    assert rebuilt.groupby("event_id")["security_id"].nunique().max() == 1
    assert output["event_id"].iloc[0] == "PEAD:001:2024-02-13"


def test_deterministic_tie_break_is_independent_of_input_order() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    d1 = _d1([("001", sessions[30], 1.0)])
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "03", sessions, 200.0),
            *_security_rows("001", "02", sessions, 200.0),
        ]
    )

    first = contract.build_event_window_contract(d1, d2a)
    second = contract.build_event_window_contract(
        d1.sample(frac=1.0, random_state=7),
        d2a.sample(frac=1.0, random_state=11),
    )

    assert first["security_id"].iloc[0] == "001-02"
    pd.testing.assert_frame_equal(first, second)


def test_iid_01_has_no_default_preference_or_fallback() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 100.0),
            *_security_rows("001", "02", sessions, 300.0),
        ]
    )
    output = contract.build_event_window_contract(_d1([("001", sessions[30], 1.0)]), d2a)
    assert output["security_id"].eq("001-02").all()

    sparse = d2a.loc[~(
        d2a["security_id"].eq("001-02")
        & pd.to_datetime(d2a["date"]).lt(sessions[25])
    )].copy()
    sparse.loc[sparse["security_id"].eq("001-01"), "dollar_volume"] = np.nan
    no_eligible = contract.build_event_window_contract(
        _d1([("001", sessions[30], 1.0)]), sparse
    )
    assert no_eligible["security_id"].isna().all()
    assert no_eligible["selection_status"].eq("no_eligible_candidate").all()
    assert not no_eligible["handoff_eligible"].any()


@pytest.mark.parametrize(
    "bad_d1,match",
    [
        (_d1([("001", "not-a-date", 1.0)]), "malformed date"),
        (_d1([("", "2024-02-13", 1.0)]), "malformed key"),
        (
            _d1([("001", "2024-02-13", 1.0), ("001", "2024-02-13", 2.0)]),
            r"duplicate \(issuer_id, event_date\)",
        ),
    ],
)
def test_duplicate_or_malformed_d1_events_fail_closed(
    bad_d1: pd.DataFrame, match: str
) -> None:
    _, _, _, d2a = _standard_contract()
    with pytest.raises(ValueError, match=match):
        contract.build_event_window_contract(bad_d1, d2a)


def test_weekend_event_day_plus_one_is_next_market_session() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    output, _, _, _ = _standard_contract(
        event_date="2024-02-03", sessions=sessions
    )
    assert output.loc[output["event_day"].eq(1), "return_date"].iloc[0] == pd.Timestamp(
        "2024-02-05"
    )


def test_authoritative_session_spine_excludes_closed_dates_from_selection_and_windows() -> None:
    raw_dates = pd.bdate_range("2024-01-02", periods=100)
    closed_date = raw_dates[20]
    sessions = raw_dates.delete(20)
    event_date = raw_dates[30]
    volume_01 = [200.0] * len(raw_dates)
    volume_02 = [100.0] * len(raw_dates)
    volume_02[20] = 1_000_000.0
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", raw_dates, volume_01),
            *_security_rows("001", "02", raw_dates, volume_02),
        ]
    )

    output = contract.build_event_window_contract(
        _d1([("001", event_date, 1.0)]),
        d2a,
        market_sessions=sessions,
    )

    assert output["security_id"].drop_duplicates().tolist() == ["001-01"]
    assert output["liquidity_observations"].iloc[0] == 20
    assert closed_date not in set(output["return_date"].dropna())
    assert output.loc[output["event_day"].eq(1), "return_date"].iloc[0] == sessions[
        sessions.searchsorted(event_date, side="right")
    ]
    events, canonical_returns, handoff_sessions = contract.prepare_strategy_handoff(
        output,
        d2a,
        market_sessions=sessions,
    )
    assert len(events) == 1
    assert not canonical_returns.duplicated(["security_id", "date"]).any()
    assert handoff_sessions.equals(sessions)


def test_missing_middle_return_is_not_compressed() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    event_date = sessions[30]
    first_after = 31
    missing_date = sessions[first_after + 9]
    rows_01 = _security_rows("001", "01", sessions, 200.0)
    rows_01 = [row for row in rows_01 if pd.Timestamp(row["date"]) != missing_date]
    d2a = pd.DataFrame(
        [*rows_01, *_security_rows("001", "02", sessions, 100.0)]
    )
    output = contract.build_event_window_contract(_d1([("001", event_date, 1.0)]), d2a)

    day_10 = output.loc[output["event_day"].eq(10)].iloc[0]
    day_11 = output.loc[output["event_day"].eq(11)].iloc[0]
    assert day_10["return_date"] == missing_date
    assert not day_10["return_row_present"]
    assert pd.isna(day_10["asset_return"])
    assert day_11["return_date"] == sessions[first_after + 10]
    assert not output["window_complete"].any()


def test_disappearing_selected_security_is_never_replaced() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=100)
    event_index = 30
    rows_01 = _security_rows("001", "01", sessions[: event_index + 6], 200.0)
    rows_02 = _security_rows("001", "02", sessions, 100.0)
    output = contract.build_event_window_contract(
        _d1([("001", sessions[event_index], 1.0)]), pd.DataFrame([*rows_01, *rows_02])
    )

    assert output["security_id"].eq("001-01").all()
    assert output.loc[output["event_day"].gt(5), "return_row_present"].eq(False).all()
    assert not output["handoff_eligible"].any()


def test_short_market_spine_still_emits_exactly_60_skeleton_rows() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=40)
    output, _, _, _ = _standard_contract(event_date=sessions[20], sessions=sessions)
    assert len(output) == 60
    assert output["event_day"].tolist() == list(range(1, 61))
    assert output["return_date"].notna().sum() == 19
    assert output.loc[output["event_day"].gt(19), "return_date"].isna().all()
    assert output["coverage_reason"].eq("insufficient_market_sessions").all()


@pytest.mark.parametrize("column,bad_value,match", [
    ("date", "bad-date", "malformed date"),
    ("security_id", "wrong", "security_id identity"),
])
def test_malformed_d2a_values_fail_closed(
    column: str, bad_value: object, match: str
) -> None:
    _, _, d1, d2a = _standard_contract()
    d2a[column] = d2a[column].astype("object")
    d2a.loc[d2a.index[0], column] = bad_value
    with pytest.raises(ValueError, match=match):
        contract.build_event_window_contract(d1, d2a)


def test_duplicate_d2a_security_date_fails_closed() -> None:
    _, _, d1, d2a = _standard_contract()
    duplicate = pd.concat([d2a, d2a.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match=r"duplicate \(security_id, date\)"):
        contract.build_event_window_contract(d1, duplicate)


def _canonical_d1_artifact() -> pd.DataFrame:
    values: dict[str, pd.Series] = {}
    for column in contract.D1_COLUMNS:
        if column in {"gvkey"}:
            values[column] = pd.Series(["001"], dtype="string")
        elif column in {"rdq", "datadate"}:
            values[column] = pd.Series([pd.Timestamp("2024-02-13")])
        elif column in {"fyearq", "n_prior_quarters"}:
            values[column] = pd.Series([2024], dtype="int64")
        elif column in {"liquidity_pass", "valid_sue"}:
            values[column] = pd.Series([True], dtype="bool")
        else:
            values[column] = pd.Series([1.0], dtype="float64")
    return pd.DataFrame(values, columns=contract.D1_COLUMNS)


def _write_bundle(
    directory: Path,
    stem: str,
    frame: pd.DataFrame,
    columns: list[str],
) -> Path:
    parquet_path = directory / f"{stem}.parquet"
    frame.to_parquet(parquet_path, index=False)
    manifest_path = directory / f"{stem}.parquet.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "parquet_file": parquet_path.name,
                "sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
                "row_count": len(frame),
                "columns": columns,
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_input_manifest_hash_and_schema_drift_fail_before_parquet_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d1_manifest = _write_bundle(
        tmp_path, "d1", _canonical_d1_artifact(), contract.D1_COLUMNS
    )
    d2a_frame = pd.DataFrame(
        [_row("001", "01", "2024-02-12")], columns=contract.D2A_COLUMNS
    )
    d2a_manifest = _write_bundle(tmp_path, "d2a", d2a_frame, contract.D2A_COLUMNS)

    d2a_data = json.loads(d2a_manifest.read_text(encoding="utf-8"))
    d2a_data["sha256"] = "0" * 64
    d2a_manifest.write_text(json.dumps(d2a_data), encoding="utf-8")
    monkeypatch.setattr(
        pd,
        "read_parquet",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Parquet read occurred before both manifests validated")
        ),
    )
    with pytest.raises(ValueError, match="D2A Parquet hash drift"):
        contract.load_validated_inputs(d1_manifest, d2a_manifest)

    d2a_data["sha256"] = hashlib.sha256(
        (tmp_path / d2a_data["parquet_file"]).read_bytes()
    ).hexdigest()
    d2a_data["columns"] = contract.D2A_COLUMNS[:-1]
    d2a_manifest.write_text(json.dumps(d2a_data), encoding="utf-8")
    with pytest.raises(ValueError, match="D2A manifest schema drift"):
        contract.load_validated_inputs(d1_manifest, d2a_manifest)


def test_manifest_path_traversal_and_actual_schema_drift_fail_closed(tmp_path: Path) -> None:
    d1_frame = _canonical_d1_artifact()
    manifest = _write_bundle(tmp_path, "d1", d1_frame, contract.D1_COLUMNS)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["parquet_file"] = "../d1.parquet"
    manifest.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="local .parquet filename"):
        contract.resolve_input_artifact(manifest, contract.D1_COLUMNS, "D1")

    drift_frame = d1_frame.drop(columns="sue_std_scaled")
    drift_manifest = _write_bundle(tmp_path, "drift", drift_frame, contract.D1_COLUMNS)
    with pytest.raises(ValueError, match="Parquet schema drift"):
        contract.resolve_input_artifact(drift_manifest, contract.D1_COLUMNS, "D1")


def test_input_reads_are_bound_to_validated_snapshots_during_path_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_d1 = _canonical_d1_artifact()
    replacement_d1 = original_d1.copy()
    replacement_d1["sue_price_scaled"] = 99.0
    original_d2a = pd.DataFrame(
        [_row("001", "01", "2024-02-12", volume=100.0)],
        columns=contract.D2A_COLUMNS,
    )
    replacement_d2a = original_d2a.copy()
    replacement_d2a["dollar_volume"] = 999.0
    d1_manifest = _write_bundle(tmp_path, "d1", original_d1, contract.D1_COLUMNS)
    d2a_manifest = _write_bundle(tmp_path, "d2a", original_d2a, contract.D2A_COLUMNS)
    d1_replacement_path = tmp_path / "d1-replacement.parquet"
    d2a_replacement_path = tmp_path / "d2a-replacement.parquet"
    replacement_d1.to_parquet(d1_replacement_path, index=False)
    replacement_d2a.to_parquet(d2a_replacement_path, index=False)
    original_hashes = {
        "d1": hashlib.sha256((tmp_path / "d1.parquet").read_bytes()).hexdigest(),
        "d2a": hashlib.sha256((tmp_path / "d2a.parquet").read_bytes()).hexdigest(),
    }
    real_read_parquet = pd.read_parquet
    call_count = 0

    def replace_path_before_pandas_read(
        source: object, *args: object, **kwargs: object
    ) -> pd.DataFrame:
        nonlocal call_count
        if call_count == 0:
            os.replace(d1_replacement_path, tmp_path / "d1.parquet")
        elif call_count == 1:
            os.replace(d2a_replacement_path, tmp_path / "d2a.parquet")
        call_count += 1
        return real_read_parquet(source, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", replace_path_before_pandas_read)
    loaded_d1, loaded_d2a, provenance = contract.load_validated_inputs(
        d1_manifest, d2a_manifest
    )

    assert call_count == 2
    assert loaded_d1["sue_price_scaled"].iloc[0] == pytest.approx(1.0)
    assert loaded_d2a["dollar_volume"].iloc[0] == pytest.approx(100.0)
    assert provenance["d1"]["parquet_sha256"] == original_hashes["d1"]
    assert provenance["d2a"]["parquet_sha256"] == original_hashes["d2a"]


def test_atomic_publication_manifest_integrity_and_cleanup(tmp_path: Path) -> None:
    output, sessions, _, _ = _standard_contract()
    out_path = tmp_path / "windows.parquet"
    manifest_path = contract.publish_contract(
        output, out_path, "synthetic", _provenance(), sessions
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_path = manifest_path.parent / manifest["output"]["parquet_file"]

    assert not out_path.exists()
    assert versioned_path.exists()
    assert manifest["output"]["sha256"] == hashlib.sha256(
        versioned_path.read_bytes()
    ).hexdigest()
    assert manifest["output"]["schema"] == contract.OUTPUT_COLUMNS
    assert manifest["assertions"]["selected_security_never_switches_within_event"]
    assert manifest["declarations"]["zero_return_imputation"] is False
    assert manifest["declarations"]["delisting_label"] is False
    assert manifest["session_spine"]["count"] == len(sessions)
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_manifest_replace_interruption_preserves_old_pointer_and_cleans_new_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, sessions, _, _ = _standard_contract()
    out_path = tmp_path / "windows.parquet"
    manifest_path = contract.publish_contract(
        output, out_path, "old", _provenance(), sessions
    )
    old_manifest_bytes = manifest_path.read_bytes()
    old_manifest = json.loads(old_manifest_bytes.decode("utf-8"))
    old_versioned = manifest_path.parent / old_manifest["output"]["parquet_file"]
    old_versioned_bytes = old_versioned.read_bytes()
    changed = output.copy()
    changed.loc[changed["event_day"].eq(1), "asset_return"] = 0.02
    real_replace = os.replace

    def fail_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise OSError("synthetic manifest interruption")
        real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="synthetic manifest interruption"):
        contract.publish_contract(changed, out_path, "new", _provenance(), sessions)

    assert manifest_path.read_bytes() == old_manifest_bytes
    assert old_versioned.read_bytes() == old_versioned_bytes
    assert len(list(tmp_path.glob("windows.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_baseexception_before_manifest_commit_preserves_pointer_and_removes_new_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, sessions, _, _ = _standard_contract()
    out_path = tmp_path / "windows.parquet"
    manifest_path = contract.publish_contract(
        output, out_path, "old", _provenance(), sessions
    )
    old_manifest_bytes = manifest_path.read_bytes()
    old_manifest = json.loads(old_manifest_bytes.decode("utf-8"))
    old_versioned = manifest_path.parent / old_manifest["output"]["parquet_file"]
    changed = output.copy()
    changed.loc[changed["event_day"].eq(1), "asset_return"] = 0.02
    real_replace = os.replace

    def interrupt_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise KeyboardInterrupt("synthetic base-exception interruption")
        real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", interrupt_manifest_replace)
    with pytest.raises(KeyboardInterrupt, match="synthetic base-exception interruption"):
        contract.publish_contract(changed, out_path, "new", _provenance(), sessions)

    assert manifest_path.read_bytes() == old_manifest_bytes
    assert old_versioned.exists()
    assert len(list(tmp_path.glob("windows.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_baseexception_after_atomic_manifest_replace_keeps_committed_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, sessions, _, _ = _standard_contract()
    out_path = tmp_path / "windows.parquet"
    manifest_path = contract.publish_contract(
        output, out_path, "old", _provenance(), sessions
    )
    old_manifest_bytes = manifest_path.read_bytes()
    changed = output.copy()
    changed.loc[changed["event_day"].eq(1), "asset_return"] = 0.02
    real_replace = os.replace

    def interrupt_after_manifest_replace(source: str | Path, destination: str | Path) -> None:
        real_replace(source, destination)
        if Path(destination) == manifest_path:
            raise KeyboardInterrupt("interrupt after completed atomic replace")

    monkeypatch.setattr(contract.os, "replace", interrupt_after_manifest_replace)
    with pytest.raises(KeyboardInterrupt, match="after completed atomic replace"):
        contract.publish_contract(changed, out_path, "new", _provenance(), sessions)

    assert manifest_path.read_bytes() != old_manifest_bytes
    committed = json.loads(manifest_path.read_text(encoding="utf-8"))
    committed_path = manifest_path.parent / committed["output"]["parquet_file"]
    assert committed_path.exists()
    assert hashlib.sha256(committed_path.read_bytes()).hexdigest() == committed["output"][
        "sha256"
    ]
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_partial_parquet_failure_and_concurrent_writer_clean_temps_and_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, sessions, _, _ = _standard_contract()
    out_path = tmp_path / "windows.parquet"
    lock_path = out_path.with_suffix(".parquet.lock")
    with contract._publication_lock(lock_path):
        with pytest.raises(RuntimeError, match="publication lock is already held"):
            contract.publish_contract(output, out_path, "locked", _provenance(), sessions)
    assert not lock_path.exists()

    def fail_to_parquet(self: pd.DataFrame, path: Path, **_kwargs: object) -> None:
        Path(path).write_bytes(b"partial")
        raise RuntimeError("synthetic parquet interruption")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail_to_parquet)
    with pytest.raises(RuntimeError, match="synthetic parquet interruption"):
        contract.publish_contract(output, out_path, "partial", _provenance(), sessions)
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))
    assert not out_path.with_suffix(".parquet.manifest.json").exists()


def test_strategy_adapter_uses_only_eligible_events_and_canonical_d2a_returns() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=110)
    complete_event = sessions[30]
    short_event = sessions[80]
    d1 = _d1(
        [("001", complete_event, 1.0), ("001", short_event, -1.0)]
    )
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 200.0),
            *_security_rows("001", "02", sessions, 100.0),
        ]
    )
    handoff = contract.build_event_window_contract(d1, d2a)
    strategy_events, strategy_returns, adapter_sessions = contract.prepare_strategy_handoff(
        handoff, d2a
    )
    windows = contract.build_strategy_event_windows(handoff, d2a)

    assert strategy_events["event_id"].tolist() == [
        f"PEAD:001:{complete_event.strftime('%Y-%m-%d')}"
    ]
    assert not strategy_returns.duplicated(["security_id", "date"]).any()
    assert adapter_sessions.equals(sessions)
    assert windows["window_complete"].all()
    assert len(windows) == 60


def test_strategy_adapter_supports_overlapping_events_without_duplicate_return_keys() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=120)
    event_dates = [sessions[30], sessions[40]]
    d1 = _d1([("001", event_dates[0], 1.0), ("001", event_dates[1], 2.0)])
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 200.0),
            *_security_rows("001", "02", sessions, 100.0),
        ]
    )
    handoff = contract.build_event_window_contract(d1, d2a)

    events, canonical_returns, adapter_sessions = contract.prepare_strategy_handoff(
        handoff, d2a
    )
    windows = contract.build_strategy_event_windows(handoff, d2a)

    assert len(events) == 2
    assert not canonical_returns.duplicated(["security_id", "date"]).any()
    assert len(canonical_returns) == len(sessions)
    assert adapter_sessions.equals(sessions)
    assert len(windows) == 120
    assert windows["window_complete"].all()
    overlap = set(
        windows.loc[windows["event_id"].eq(events["event_id"].iloc[0]), "return_date"]
    ).intersection(
        windows.loc[windows["event_id"].eq(events["event_id"].iloc[1]), "return_date"]
    )
    assert overlap


def test_strategy_adapter_validates_full_d2a_in_chunks_before_selected_return_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = pd.bdate_range("2024-01-02", periods=110)
    event_date = sessions[30]
    d1 = _d1([("001", event_date, 1.0)])
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 200.0),
            *_security_rows("001", "02", sessions, 100.0),
        ]
    )
    handoff = contract.build_event_window_contract(d1, d2a)
    monkeypatch.setattr(contract, "HANDOFF_VALIDATION_CHUNK_ROWS", 17)

    def reject_full_normalisation(_frame: pd.DataFrame) -> pd.DataFrame:
        raise AssertionError("strategy handoff must not normalise the full D2A frame")

    monkeypatch.setattr(contract, "_normalise_d2a", reject_full_normalisation)
    events, canonical_returns, adapter_sessions = contract.prepare_strategy_handoff(
        handoff,
        d2a,
    )

    assert len(events) == 1
    assert str(canonical_returns["security_id"].dtype) == "category"
    assert canonical_returns["security_id"].nunique() == 1
    assert adapter_sessions.equals(sessions)

    invalid_unselected = d2a.copy()
    invalid_unselected.loc[invalid_unselected["security_id"].eq("001-02"), "dollar_volume"] = -1.0
    with pytest.raises(ValueError, match="negative"):
        contract.prepare_strategy_handoff(handoff, invalid_unselected)


def test_strategy_adapter_rejects_cross_row_event_metadata_drift() -> None:
    output, sessions, _, d2a = _standard_contract()
    event_id = output.loc[output["handoff_eligible"], "event_id"].iloc[0]
    malformed = output.copy()
    day_one = malformed["event_id"].eq(event_id) & malformed["event_day"].eq(1)
    malformed.loc[day_one, "event_date"] = malformed.loc[day_one, "event_date"] + pd.Timedelta(
        days=90
    )

    with pytest.raises(ValueError, match="event_date is inconsistent"):
        contract.prepare_strategy_handoff(malformed, d2a, sessions)


def test_strategy_adapter_rejects_normalized_duplicate_on_unselected_security() -> None:
    sessions = pd.bdate_range("2024-01-02", periods=110)
    event_date = sessions[30]
    d1 = _d1([("001", event_date, 1.0)])
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 200.0),
            *_security_rows("001", "02", sessions, 100.0),
        ]
    )
    handoff = contract.build_event_window_contract(d1, d2a)
    duplicate = d2a.loc[d2a["security_id"].eq("001-02")].iloc[[0]].copy()
    duplicate["security_id"] = " 001-02 "
    malformed = pd.concat([d2a, duplicate], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate normalized"):
        contract.prepare_strategy_handoff(handoff, malformed)


def test_cli_normalises_full_d2a_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, sessions, d1, d2a = _standard_contract()
    calls = 0
    real_normalise = contract._normalise_d2a

    def counting_normalise(frame: pd.DataFrame) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        return real_normalise(frame)

    monkeypatch.setattr(contract, "_normalise_d2a", counting_normalise)
    monkeypatch.setattr(contract, "SAMPLE_N_GVKEYS", 1)
    monkeypatch.setattr(contract, "OUT_SAMPLE_PATH", tmp_path / "windows.parquet")
    monkeypatch.setattr(
        contract,
        "load_validated_inputs",
        lambda: (d1, d2a, _provenance()),
    )
    monkeypatch.setattr(
        contract,
        "_load_authoritative_market_sessions",
        lambda _path: (
            sessions,
            {
                "kind": "synthetic_market_sessions",
                "use": "test_only",
            },
        ),
    )

    contract.main(["--sample"])

    assert calls == 1
    manifest = json.loads(
        (tmp_path / "windows.parquet.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["session_spine"]["count"] == len(sessions)


def test_output_schema_is_exact_and_null_asset_returns_are_not_imputed() -> None:
    output, _, _, _ = _standard_contract()
    assert list(output.columns) == contract.OUTPUT_COLUMNS
    assert output["return_row_present"].all()
    assert output["handoff_eligible"].all()

    sessions = pd.bdate_range("2024-01-02", periods=100)
    returns = [0.01] * len(sessions)
    returns[40] = None
    d2a = pd.DataFrame(
        [
            *_security_rows("001", "01", sessions, 200.0, returns),
            *_security_rows("001", "02", sessions, 100.0),
        ]
    )
    null_output = contract.build_event_window_contract(
        _d1([("001", sessions[30], 1.0)]), d2a
    )
    row = null_output.loc[null_output["return_date"].eq(sessions[40])].iloc[0]
    assert row["return_row_present"]
    assert pd.isna(row["asset_return"])
    assert row["return_type"] == "unavailable"
    assert not row["window_complete"]


def test_full_build_consumes_d2a_bounded_and_matches_in_memory_semantics(
    tmp_path: Path,
) -> None:
    expected, sessions, _, d2a = _standard_contract()
    canonical_d1 = _canonical_d1_artifact()
    canonical_d1["sue_price_scaled"] = 1.25
    canonical_d1["sue_price_scaled_clipped"] = 1.25
    d1_manifest = _write_bundle(
        tmp_path, "d1", canonical_d1, contract.D1_COLUMNS
    )
    d2a_manifest = _write_bundle(tmp_path, "d2a", d2a, contract.D2A_COLUMNS)
    out_path = tmp_path / "windows.parquet"

    with pytest.MonkeyPatch.context() as bounded:
        bounded.setattr(
            contract,
            "_capture_input_snapshot",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full build must not capture whole Parquet bytes")
            ),
        )
        bounded.setattr(
            pd,
            "read_parquet",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full D2A must not be loaded as a pandas frame")
            ),
        )
        bounded.setattr(
            contract,
            "_normalise_d2a",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full D2A must remain lazy")
            ),
        )
        bounded.setattr(
            pd.DataFrame,
            "to_parquet",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("full D2B output must not be a pandas frame")
            ),
        )
        manifest_path = contract.build_full_contract(
            d1_manifest,
            d2a_manifest,
            out_path,
            sessions,
            session_source={"kind": "synthetic", "use": "test_only"},
            label="fixture_full",
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_path = manifest_path.parent / manifest["output"]["parquet_file"]
    actual = pd.read_parquet(versioned_path)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
    assert not out_path.exists()
    assert manifest["output"]["sha256"] == contract._sha256_file(versioned_path)
    assert manifest["counts"]["events"] == expected["event_id"].nunique()
    assert manifest["assertions"]["selected_security_never_switches_within_event"]
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_full_build_invalid_unselected_d2a_fails_closed_without_publication(
    tmp_path: Path,
) -> None:
    _, sessions, _, d2a = _standard_contract()
    d2a.loc[d2a["security_id"].eq("001-02"), "dollar_volume"] = -1.0
    d1_manifest = _write_bundle(
        tmp_path, "d1", _canonical_d1_artifact(), contract.D1_COLUMNS
    )
    d2a_manifest = _write_bundle(tmp_path, "d2a", d2a, contract.D2A_COLUMNS)
    out_path = tmp_path / "windows.parquet"

    with pytest.raises(ValueError, match="negative"):
        contract.build_full_contract(
            d1_manifest, d2a_manifest, out_path, sessions
        )
    assert not out_path.with_suffix(".parquet.manifest.json").exists()
    assert not list(tmp_path.glob("windows.*.parquet"))
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_full_build_manifest_interruption_preserves_old_pointer_and_cleans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, sessions, _, d2a = _standard_contract()
    d1_manifest = _write_bundle(
        tmp_path, "d1", _canonical_d1_artifact(), contract.D1_COLUMNS
    )
    d2a_manifest = _write_bundle(tmp_path, "d2a", d2a, contract.D2A_COLUMNS)
    out_path = tmp_path / "windows.parquet"
    manifest_path = contract.build_full_contract(
        d1_manifest, d2a_manifest, out_path, sessions, label="old"
    )
    old_manifest_bytes = manifest_path.read_bytes()
    changed = d2a.copy()
    selected_day = changed["security_id"].eq("001-01") & pd.to_datetime(
        changed["date"]
    ).eq(sessions[31])
    changed.loc[selected_day, "total_return"] = 0.02
    d2a_manifest = _write_bundle(
        tmp_path, "d2a", changed, contract.D2A_COLUMNS
    )
    real_replace = os.replace

    def fail_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise OSError("synthetic full-build manifest interruption")
        real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="synthetic full-build manifest interruption"):
        contract.build_full_contract(
            d1_manifest, d2a_manifest, out_path, sessions, label="new"
        )

    assert manifest_path.read_bytes() == old_manifest_bytes
    assert len(list(tmp_path.glob("windows.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))
