from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import duckdb

from research.prebreakout_discovery_v1 import trial1_m0
from research.prebreakout_discovery_v1.precharge_custody import (
    CODE_BUNDLE_PATHS,
    build_code_bundle_manifest,
    build_trial1_source_manifest,
    compute_development_label_hash,
    compute_episode_anchor_hash,
    create_market_table,
    decision_spine_hash,
    stream_record_hash,
)


def _dates(count: int) -> list[str]:
    start = date(2025, 1, 1)
    return [(start + timedelta(days=index)).isoformat() for index in range(count)]


def _write_market_fixture(tmp_path: Path) -> tuple[Path, list[str]]:
    dates = _dates(246)
    path = tmp_path / "market.csv"
    lines = [
        "SP_CIQ_ID,SP_TRADING_ITEM_ID,MEMBERSHIP_AS_OF_DATE,SP_PRICE_CLOSE,SP_TOTAL_RETURN"
    ]
    for index, session in enumerate(dates):
        close = 101.0 if index == 20 else 100.0
        lines.append(f"IQ1001,1001,{session},{close},1.0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, dates


def test_hash_only_label_and_episode_custody_is_deterministic(tmp_path: Path) -> None:
    market_path, dates = _write_market_fixture(tmp_path)
    decisions = dates[:226]
    counts = {session: 1 for session in decisions}

    connection = duckdb.connect(database=":memory:")
    try:
        create_market_table(
            connection,
            csv_paths=[market_path.as_posix()],
            maximum_session_date=dates[-1],
        )
        first_labels = compute_development_label_hash(
            connection,
            decision_dates=decisions,
            candidate_counts=counts,
        )
        second_labels = compute_development_label_hash(
            connection,
            decision_dates=decisions,
            candidate_counts=counts,
        )
        first_episodes = compute_episode_anchor_hash(
            connection,
            session_spine=dates,
            development_decision_dates=decisions,
        )
        second_episodes = compute_episode_anchor_hash(
            connection,
            session_spine=dates,
            development_decision_dates=decisions,
        )
    finally:
        connection.close()

    assert first_labels.payload_sha256 == second_labels.payload_sha256
    assert first_labels.record_count == second_labels.record_count == 226
    assert first_episodes.payload_sha256 == second_episodes.payload_sha256
    assert first_episodes.record_count >= 1
    assert list(tmp_path.glob("*label*")) == []
    assert list(tmp_path.glob("*episode*")) == []


def test_stream_hash_is_order_sensitive() -> None:
    rows = [{"x": 1}, {"x": 2}]
    first, count = stream_record_hash("FIXTURE:DOMAIN", rows)
    second, _ = stream_record_hash("FIXTURE:DOMAIN", list(reversed(rows)))
    assert count == 2
    assert first != second


def test_code_bundle_and_source_manifest_are_exact_and_uncharged(tmp_path: Path) -> None:
    for relative in CODE_BUNDLE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {relative}\n", encoding="utf-8")
    code = build_code_bundle_manifest(tmp_path)
    assert len(code["files"]) == 4
    assert len(code["code_bundle_sha256"]) == 64

    manifest = build_trial1_source_manifest(
        market_history_payload_sha256="a" * 64,
        w3_pit_authority_bundle_sha256="b" * 64,
        development_label_custody_sha256="c" * 64,
        episode_custody_sha256="d" * 64,
        decision_spine_sha256="e" * 64,
        source_receipt_bundle_sha256="f" * 64,
    )
    assert trial1_m0.verify_trial1_source_manifest(manifest) == manifest["manifest_sha256"]
    prepared = trial1_m0.prepare_trial1_m0_for_trial_open(
        source_manifest=manifest,
        code_sha256=code["code_bundle_sha256"],
    )
    assert prepared.trial_open_appended is False
    assert prepared.trial_cost == 1
    assert decision_spine_hash(_dates(226)) != ""