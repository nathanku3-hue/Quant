from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from research.prebreakout_discovery_v1.ledger import (
    append_trial_close,
    append_trial_open,
    load_trial_ledger,
)


BASE = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def _variant(index: int) -> dict[str, str]:
    return {
        "implementation_id": f"PREBREAKOUT_DEV_{index:02d}",
        "feature_spec_id": f"FEATURES_{index:02d}",
        "transform_spec_id": f"TRANSFORMS_{index:02d}",
        "model_spec_id": f"MODEL_{index:02d}",
        "training_window_spec_id": "ROLLING_EXPANDING_WF_V1",
        "calibration_spec_id": "NO_CALIBRATION_V1",
        "ranking_spec_id": "DATE_LOCAL_RANK_V1",
        "control_spec_id": "BREADTH_MATCHED_CONTROL_V1",
        "cross_sectional_holdout_spec_id": "HASH_BUCKET_HOLDOUT_V1",
        "temporal_fold_plan_id": "FOUR_TEMPORAL_OOS_FOLDS_WHERE_LEGITIMATE_V1",
        "source_manifest_sha256": f"{index + 1:064x}",
        "code_sha256": f"{index + 101:064x}",
    }


def test_trial_open_charges_before_result_and_close_never_refunds_failure(tmp_path: Path) -> None:
    ledger = tmp_path / "prebreakout_trials.jsonl"
    opened = append_trial_open(
        ledger,
        trial_id="trial-01",
        variant=_variant(0),
        recorded_at=BASE,
    )
    assert opened["event_type"] == "TRIAL_OPEN"
    assert opened["cumulative_material_trials"] == 1
    assert opened["payload"]["untouched_lockbox_access"] == "FORBIDDEN"
    assert opened["payload"]["prospective_outcome_access"] == "FORBIDDEN"

    closed = append_trial_close(
        ledger,
        trial_id="trial-01",
        result_status="FAILED",
        result_artifact_sha256="f" * 64,
        result_summary={"reason": "synthetic_failure"},
        recorded_at=BASE + timedelta(seconds=1),
    )
    assert closed["event_type"] == "TRIAL_CLOSE"
    assert closed["cumulative_material_trials"] == 1
    assert closed["payload"]["result_status"] == "FAILED"

    second = append_trial_open(
        ledger,
        trial_id="trial-02",
        variant=_variant(1),
        recorded_at=BASE + timedelta(seconds=2),
    )
    assert second["cumulative_material_trials"] == 2


def test_trial_budget_is_hard_eight_and_ninth_open_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "prebreakout_trials.jsonl"
    for index in range(8):
        entry = append_trial_open(
            ledger,
            trial_id=f"trial-{index + 1:02d}",
            variant=_variant(index),
            recorded_at=BASE + timedelta(seconds=index),
        )
        assert entry["cumulative_material_trials"] == index + 1

    with pytest.raises(ValueError, match="trial_budget_exceeded"):
        append_trial_open(
            ledger,
            trial_id="trial-09",
            variant=_variant(8),
            recorded_at=BASE + timedelta(seconds=9),
        )
    assert len(load_trial_ledger(ledger)) == 8


def test_trial_ledger_is_hash_chained_unique_and_close_requires_open(tmp_path: Path) -> None:
    ledger = tmp_path / "prebreakout_trials.jsonl"
    first = append_trial_open(
        ledger,
        trial_id="trial-01",
        variant=_variant(0),
        recorded_at=BASE,
    )
    second = append_trial_close(
        ledger,
        trial_id="trial-01",
        result_status="COMPLETE",
        result_artifact_sha256="a" * 64,
        result_summary={"folds_completed": 4},
        recorded_at=BASE + timedelta(seconds=1),
    )
    tape = load_trial_ledger(ledger)
    assert tape == [first, second]
    assert first["sequence"] == 0
    assert first["previous_chain_hash"] == "0" * 64
    assert second["sequence"] == 1
    assert second["previous_chain_hash"] == first["chain_hash"]

    with pytest.raises(FileExistsError, match="trial_already_opened"):
        append_trial_open(
            ledger,
            trial_id="trial-01",
            variant=_variant(0),
            recorded_at=BASE + timedelta(seconds=2),
        )
    with pytest.raises(FileExistsError, match="trial_already_closed"):
        append_trial_close(
            ledger,
            trial_id="trial-01",
            result_status="FAILED",
            result_artifact_sha256="b" * 64,
            recorded_at=BASE + timedelta(seconds=3),
        )
    with pytest.raises(ValueError, match="close_without_open"):
        append_trial_close(
            ledger,
            trial_id="trial-never-opened",
            result_status="FAILED",
            result_artifact_sha256="c" * 64,
            recorded_at=BASE + timedelta(seconds=4),
        )


def test_trial_ledger_detects_tamper_partial_line_and_writer_lock(tmp_path: Path) -> None:
    ledger = tmp_path / "prebreakout_trials.jsonl"
    append_trial_open(
        ledger,
        trial_id="trial-01",
        variant=_variant(0),
        recorded_at=BASE,
    )
    parsed = json.loads(ledger.read_text(encoding="utf-8").strip())
    parsed["payload"]["variant"]["model_spec_id"] = "TAMPERED"
    ledger.write_text(json.dumps(parsed, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="chain_hash_mismatch"):
        load_trial_ledger(ledger)

    ledger.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="partial_final_line"):
        load_trial_ledger(ledger)

    ledger.unlink()
    lock = Path(str(ledger) + ".lock")
    lock.write_text("other-writer\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="writer_lock_exists"):
        append_trial_open(
            ledger,
            trial_id="trial-02",
            variant=_variant(1),
            recorded_at=BASE + timedelta(seconds=5),
        )
    assert lock.exists()


def test_trial_variant_requires_explicit_scientific_identity_and_sha256s(tmp_path: Path) -> None:
    ledger = tmp_path / "prebreakout_trials.jsonl"
    bad = _variant(0)
    bad.pop("cross_sectional_holdout_spec_id")
    with pytest.raises(ValueError, match="cross_sectional_holdout_spec_id_required"):
        append_trial_open(ledger, trial_id="trial-01", variant=bad, recorded_at=BASE)

    bad = _variant(0)
    bad["code_sha256"] = "not-a-hash"
    with pytest.raises(ValueError, match="code_sha256_invalid"):
        append_trial_open(ledger, trial_id="trial-02", variant=bad, recorded_at=BASE)
