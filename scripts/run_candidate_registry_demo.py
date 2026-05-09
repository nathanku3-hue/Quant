from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.provenance import load_manifest
from data.provenance import utc_now_iso
from v2_discovery.registry import DEFAULT_EVENT_LOG_PATH
from v2_discovery.registry import DEFAULT_REBUILD_REPORT_PATH
from v2_discovery.registry import DEFAULT_SNAPSHOT_PATH
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateRegistryError
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


DEMO_CANDIDATE_ID = "PH65_PEAD_DUMMY_001"
DEMO_MANIFEST_URI = "data/processed/phase56_pead_evidence.csv.manifest.json"


def _repo_root() -> Path:
    return REPO_ROOT


def _code_ref(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "git_ref_unavailable"


def _demo_spec(repo_root: Path) -> CandidateSpec:
    manifest = load_manifest(repo_root / DEMO_MANIFEST_URI)
    return CandidateSpec(
        candidate_id=DEMO_CANDIDATE_ID,
        family_id="PEAD_DAILY_RESEARCH",
        hypothesis="Post-earnings drift candidate placeholder for registry test only.",
        universe="US_EQUITIES_DAILY",
        features=("earnings_surprise_placeholder", "liquidity_filter_placeholder"),
        parameters_searched={"holding_days": [1, 5, 10], "liquidity_floor": ["placeholder"]},
        trial_count=6,
        train_window={"start": "2014-01-01", "end": "2021-12-31"},
        test_window={"start": "2022-01-01", "end": "2024-12-31"},
        cost_model={"commission_bps": 0, "slippage_bps": 10},
        data_snapshot={"dataset": "phase56_pead_evidence", "asof": manifest["asof_ts"]},
        manifest_uri=DEMO_MANIFEST_URI,
        source_quality=manifest["source_quality"],
        created_at=utc_now_iso(),
        created_by="phase65_demo",
        code_ref=_code_ref(repo_root),
        status=CandidateStatus.GENERATED,
    )


def run_demo() -> dict[str, object]:
    repo_root = _repo_root()
    registry = CandidateRegistry(
        DEFAULT_EVENT_LOG_PATH,
        snapshot_path=DEFAULT_SNAPSHOT_PATH,
        repo_root=repo_root,
    )

    snapshot = registry.rebuild_snapshot()
    if DEMO_CANDIDATE_ID not in snapshot:
        spec = _demo_spec(repo_root)
        registry.register_candidate(spec, actor="phase65_demo")
        registry.change_status(
            DEMO_CANDIDATE_ID,
            CandidateStatus.INCUBATING,
            actor="phase65_demo",
            reason="dummy lifecycle proof",
        )
        registry.reject_candidate(
            DEMO_CANDIDATE_ID,
            actor="phase65_demo",
            reason="dummy candidate rejected after registry lifecycle proof",
        )
    else:
        status = snapshot[DEMO_CANDIDATE_ID].status
        if status == CandidateStatus.GENERATED:
            registry.change_status(
                DEMO_CANDIDATE_ID,
                CandidateStatus.INCUBATING,
                actor="phase65_demo",
                reason="resume dummy lifecycle proof",
            )
            registry.reject_candidate(
                DEMO_CANDIDATE_ID,
                actor="phase65_demo",
                reason="dummy candidate rejected after registry lifecycle proof",
            )
        elif status == CandidateStatus.INCUBATING:
            registry.reject_candidate(
                DEMO_CANDIDATE_ID,
                actor="phase65_demo",
                reason="resume dummy lifecycle proof",
            )
        elif status != CandidateStatus.REJECTED:
            raise CandidateRegistryError(
                f"Demo candidate already exists in unexpected status: {status.value}"
            )

    snapshot_path = registry.write_snapshot()
    report_path = registry.write_rebuild_report(
        DEFAULT_REBUILD_REPORT_PATH,
        demo_candidate_id=DEMO_CANDIDATE_ID,
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["snapshot_written"] = snapshot_path.as_posix()
    report["report_written"] = report_path.as_posix()
    report["manifest_exists"] = (repo_root / DEMO_MANIFEST_URI).exists()
    return report


def main() -> None:
    print(json.dumps(run_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
