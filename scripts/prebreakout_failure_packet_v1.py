"""Build FailurePacketV1 from already-opened Trial #1 development evidence only.

This command is deliberately read-only with respect to Trial #1 data custody,
the trial ledger, provider sources, the successor methodology, prediction
clocks, and W6.  Its sole write is the requested diagnostic evidence packet.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping

import duckdb
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.prebreakout_discovery_v1.failure_packet_v1 import build_failure_packet
from research.prebreakout_pit_v1.real_source import sha256_file
from scripts.prebreakout_run_trial1_w4_w5 import _load_w3, _smoke_development_checks


TRIAL_ROOT = Path("data/prebreakout/compiled/trial1_real_20260810")
DEFAULT_OUTPUT = Path("docs/context/e2e_evidence/prebreakout_failure_packet_v1_20260810.json")
ECONPHYSICS_MANIFEST = Path("docs/architecture/econphysics_prebreakout_v1_pit_observable_manifest.json")
A2_RESULT = Path("data/aov0/historical/evidence/a2_result.json")
WINNER_CAPTURE = Path("docs/context/e2e_evidence/winner_capture_diagnostic_v0_20260810.json")


class FailurePacketRunError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise FailurePacketRunError(f"failure_packet_json_object_required:{path}")
    return value


def _load_gzip_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise FailurePacketRunError(f"failure_packet_json_object_required:{path}")
    return value


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def _read_trial_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    flags = TRIAL_ROOT / "trial1_flag_projection.parquet"
    labels = TRIAL_ROOT / "development_labels.parquet"
    winners = TRIAL_ROOT / "w4_winner_stage.parquet"
    false_winners = TRIAL_ROOT / "w4_false_stage.parquet"
    for path in (flags, labels, winners, false_winners):
        if not path.is_file():
            raise FileNotFoundError(path)

    connection = duckdb.connect(database=":memory:")
    try:
        facts = connection.execute(
            """
            SELECT
                f.decision_session_date AS decision_date,
                f.security_id,
                f.trading_item_id,
                f.feature_status,
                f.near_high_component,
                f.vol_compression_component,
                f.volume_pressure_component,
                f.flagged,
                CAST(l.forward_total_return AS DOUBLE) AS forward_total_return,
                l.winner_label
            FROM read_parquet(?) f
            JOIN read_parquet(?) l
              ON l.decision_session_date = f.decision_session_date
             AND l.security_id = f.security_id
             AND l.trading_item_id = f.trading_item_id
            WHERE f.eligibility_status = 'ELIGIBLE'
            ORDER BY f.decision_session_date, f.security_id
            """,
            [str(flags), str(labels)],
        ).df()
        winner_frame = connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY breakout_session_ordinal, security_id, trading_item_id",
            [str(winners)],
        ).df()
        false_frame = connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY decision_session_ordinal, security_id, trading_item_id",
            [str(false_winners)],
        ).df()
    finally:
        connection.close()
    flag_frame = pd.read_parquet(flags)
    return facts, winner_frame, false_frame, flag_frame


def run(output: Path) -> dict[str, Any]:
    w5_path = TRIAL_ROOT / "w5_development_run.json.gz"
    flag_path = TRIAL_ROOT / "trial1_flag_projection.parquet"
    winner_path = TRIAL_ROOT / "w4_winner_stage.parquet"
    false_path = TRIAL_ROOT / "w4_false_stage.parquet"
    label_path = TRIAL_ROOT / "development_labels.parquet"
    close_path = TRIAL_ROOT / "trial1_development_result.json"

    w5_run = _load_gzip_json(w5_path)
    trial_close = _load_json(close_path)
    if trial_close.get("economic_status") != "FAIL":
        raise FailurePacketRunError("failure_packet_requires_closed_failed_trial1")
    if trial_close.get("w6_lockbox_opened") is not False or trial_close.get("w6_labels_opened") is not False:
        raise FailurePacketRunError("failure_packet_w6_must_remain_unopened")
    if trial_close.get("material_trials_consumed") != 1:
        raise FailurePacketRunError("failure_packet_trial_budget_truth_drift")

    facts, winners, false_winners, flags = _read_trial_frames()
    source, _authority, partition = _load_w3()
    smoke_check = _smoke_development_checks(
        flag_path=flag_path,
        source=source,
        partition=partition,
    )

    source_sha256s = {
        "trial1_development_result_json": sha256_file(close_path),
        "w5_development_run_json_gz": sha256_file(w5_path),
        "trial1_flag_projection_parquet": sha256_file(flag_path),
        "development_labels_parquet": sha256_file(label_path),
        "w4_winner_stage_parquet": sha256_file(winner_path),
        "w4_false_stage_parquet": sha256_file(false_path),
        "sealed_w4_discovery_atlas_json_gz": sha256_file(TRIAL_ROOT / "w4_discovery_atlas.json.gz"),
        "econphysics_prebreakout_v1_pit_observable_manifest": sha256_file(ECONPHYSICS_MANIFEST),
        "a2_result_json": sha256_file(A2_RESULT),
        "winner_capture_diagnostic_v0": sha256_file(WINNER_CAPTURE),
    }

    packet = build_failure_packet(
        w5_run=w5_run,
        eligible_labeled_features=facts,
        winner_census=winners,
        flag_projection=flags,
        false_winners=false_winners,
        smoke_check=smoke_check,
        econphysics_manifest=_load_json(ECONPHYSICS_MANIFEST),
        a2_result=_load_json(A2_RESULT),
        winner_capture_diagnostic=_load_json(WINNER_CAPTURE),
        source_sha256s=source_sha256s,
    )
    output_sha256 = _atomic_json(output, packet)
    return {
        "status": "FAILURE_PACKET_V1_WRITTEN",
        "output": str(output),
        "output_sha256": output_sha256,
        "packet_sha256": packet["packet_sha256"],
        "trial_cost": packet["authority"]["trial_cost"],
        "capture_authority": packet["authority"]["capture_authority"],
        "successor_empirical_trial_authority": packet["authority"]["successor_empirical_trial_authority"],
        "w6_authority": packet["authority"]["w6_authority"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
