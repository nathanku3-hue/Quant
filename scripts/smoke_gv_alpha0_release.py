"""Fresh-workspace smoke for the packaged GV-ALPHA0 paper-decision product."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_alpha0_ship_runtime import prepare_runtime_workspace
from core.gv_v2_alpha0_case_close import (
    FUNCTIONAL_STAGE_OPERABLE,
    FUNCTIONAL_STAGE_PRE_ADJUDICATION,
    OPERATOR_CONFIRMATION_PHRASE,
)
from views.gv_alpha0_case_workspace import (
    apply_operator_confirmation,
    load_workspace_model,
)



def run_smoke(data_dir: Path) -> dict[str, str | bool]:
    workspace = prepare_runtime_workspace(bundle_root=ROOT, runtime_root=data_dir)
    before = load_workspace_model(root=workspace.root, verify=True)
    if before.get("functional_stage") != FUNCTIONAL_STAGE_PRE_ADJUDICATION:
        raise SystemExit("SMOKE_EXPECTED_PRE_ADJUDICATION")

    confirmed = apply_operator_confirmation(
        root=workspace.root,
        adjudicator_label="FRESH_MACHINE_SMOKE",
        confirmation_phrase=OPERATOR_CONFIRMATION_PHRASE,
        confirmed_at="2026-07-28T04:00:00.000000Z",
    )
    if confirmed.get("functional_stage") != FUNCTIONAL_STAGE_OPERABLE:
        raise SystemExit("SMOKE_CONFIRM_DID_NOT_REACH_OPERABLE")

    reopened_workspace = prepare_runtime_workspace(
        bundle_root=ROOT, runtime_root=data_dir
    )
    reopened = load_workspace_model(root=reopened_workspace.root, verify=True)
    if reopened.get("functional_stage") != FUNCTIONAL_STAGE_OPERABLE:
        raise SystemExit("SMOKE_REOPEN_DID_NOT_PERSIST_OPERABLE")
    if not reopened.get("operator_confirmation_present"):
        raise SystemExit("SMOKE_REOPEN_CONFIRMATION_MISSING")

    return {
        "status": "PASS",
        "initialized": workspace.initialized,
        "reopen_initialized": reopened_workspace.initialized,
        "functional_stage": str(reopened["functional_stage"]),
        "portfolio_action": str(reopened["portfolio_action_invariant"]),
        "seed_digest": workspace.seed_digest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args(argv)

    if args.data_dir is not None:
        record = run_smoke(args.data_dir.expanduser().absolute())
    else:
        with tempfile.TemporaryDirectory(prefix="gv-alpha0-smoke-") as tmp:
            record = run_smoke(Path(tmp) / "runtime")
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
