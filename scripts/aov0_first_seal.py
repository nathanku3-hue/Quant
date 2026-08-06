"""Fail-closed local entrypoint for the first real AOV-0 prospective seal."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.aov0.cash import build_economic_cash_returns
from research.aov0.contracts import (
    AOV0Contract,
    DEFAULT_CONTRACT,
    OWNER_INSURANCE_DECISION_FIELDS,
)
from research.aov0.cube import build_vertical_cube
from research.aov0.experiment import run_five_arm_experiment, seal_prospective_experiment


DEFAULT_INPUT_ROOT = Path("data/aov0/current")
DEFAULT_OUTPUT_ROOT = Path("data/aov0")
REQUIRED_INPUTS = {
    "rule100_targets": "rule100_targets.parquet",
    "vertical_primitives": "vertical_primitives.parquet",
    "total_returns": "total_returns.parquet",
    "official_sofr": "official_sofr.parquet",
    "decision_cut": "decision_cut.json",
}


def _load_wide(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "date" not in frame.columns:
        raise ValueError(f"aov0_first_seal_date_column_required:{path}")
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame = frame.set_index("date").sort_index()
    try:
        frame.columns = pd.Index([int(column) for column in frame.columns], dtype="int64", name="permno")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"aov0_first_seal_permno_columns_required:{path}") from exc
    return frame.astype(float)


def run_first_seal(
    *,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    contract: AOV0Contract = DEFAULT_CONTRACT,
) -> dict[str, object]:
    input_root = Path(input_root)
    paths = {name: input_root / filename for name, filename in REQUIRED_INPUTS.items()}
    missing = [name for name, path in paths.items() if not path.is_file()]
    owner_decisions = [
        field
        for field in OWNER_INSURANCE_DECISION_FIELDS
        if getattr(contract, field) is None
    ]
    if owner_decisions or missing:
        if owner_decisions and missing:
            status = "BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS"
        elif owner_decisions:
            status = "BLOCKED_OWNER_DECISION"
        else:
            status = "BLOCKED_MISSING_ADMITTED_INPUTS"
        return {
            "status": status,
            "alpha_evidence": 0,
            "prospective_clock_started": False,
            "owner_decisions_required": owner_decisions,
            "missing": missing,
            "required_paths": {name: path.as_posix() for name, path in paths.items()},
        }

    rule100 = _load_wide(paths["rule100_targets"])
    returns = _load_wide(paths["total_returns"])
    primitives = pd.read_parquet(paths["vertical_primitives"])
    sofr = pd.read_parquet(paths["official_sofr"])
    cut = json.loads(paths["decision_cut"].read_text(encoding="utf-8"))
    decision_cut_id = str(cut.get("decision_cut_id") or "").strip()
    sealed_at = str(cut.get("sealed_at") or "").strip()
    if not decision_cut_id or not sealed_at:
        raise ValueError("aov0_first_seal_decision_cut_invalid")
    if not rule100.index.equals(returns.index):
        raise ValueError("aov0_first_seal_rule100_return_calendar_mismatch")

    cube = build_vertical_cube(primitives, computed_at=sealed_at, contract=contract)
    economic_cash = build_economic_cash_returns(rule100.index, sofr)
    eligible_by_date = {
        date: tuple(sorted(group["permno"].astype(int).unique().tolist()))
        for date, group in cube.frame.groupby("date", sort=False)
    }

    experiment = run_five_arm_experiment(
        rule100_weights=rule100,
        returns_df=returns,
        economic_cash_returns=economic_cash,
        cube=cube,
        pit_eligibility_provider=lambda date: eligible_by_date.get(pd.Timestamp(date).normalize(), ()),
        output_root=Path(output_root) / "evidence",
        contract=contract,
    )
    seal = seal_prospective_experiment(
        experiment,
        cube=cube,
        decision_cut_id=decision_cut_id,
        sealed_at=sealed_at,
        output_dir=Path(output_root) / "prospective_seals",
        contract=contract,
    )
    return {
        "status": "SEALED_NOT_OPENED",
        "alpha_evidence": 0,
        "prospective_clock_started": True,
        "experiment_id": experiment.experiment_id,
        "seal_id": seal.seal_id,
        "seal_path": seal.path.as_posix(),
        "outcome_open_not_before": seal.payload["outcome_open_not_before"],
    }


def main() -> int:
    result = run_first_seal()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("prospective_clock_started") else 2


if __name__ == "__main__":
    raise SystemExit(main())
