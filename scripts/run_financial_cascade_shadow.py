"""Run the shadow-only Leningrad cascade challenger through Quant's engine."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from typing import Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.financial_cascade_shadow import (  # noqa: E402
    CascadePromotionThresholds,
    StressWindow,
    run_financial_cascade_shadow,
)
from strategies.financial_cascade import (  # noqa: E402
    FinancialCascadeObservation,
    FinancialCascadePolicy,
    load_verified_leningrad_bundle,
)


OBSERVATION_MANIFEST_SCHEMA = "quant-financial-cascade-observations-v1"


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.DatetimeIndex(frame.index)
    frame.index.name = "date"
    return frame.apply(pd.to_numeric, errors="raise")


def _load_observations(path: Path) -> tuple[FinancialCascadeObservation, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "observations"}:
        raise ValueError("CASCADE_OBSERVATION_MANIFEST_FIELDS_INVALID")
    if raw.get("schema_version") != OBSERVATION_MANIFEST_SCHEMA:
        raise ValueError("CASCADE_OBSERVATION_MANIFEST_SCHEMA_INVALID")
    rows = raw.get("observations")
    if not isinstance(rows, list):
        raise ValueError("CASCADE_OBSERVATION_MANIFEST_ROWS_REQUIRED")
    observations: list[FinancialCascadeObservation] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "effective_date",
            "source_as_of_utc",
            "available_at_utc",
            "bundle_path",
            "expected_bundle_identity",
        }:
            raise ValueError("CASCADE_OBSERVATION_ROW_FIELDS_INVALID")
        bundle_path = Path(str(row["bundle_path"]))
        if not bundle_path.is_absolute():
            bundle_path = path.parent / bundle_path
        bundle = load_verified_leningrad_bundle(
            bundle_path,
            expected_bundle_identity=str(row["expected_bundle_identity"]),
        )
        observations.append(
            FinancialCascadeObservation(
                effective_date=str(row["effective_date"]),
                source_as_of_utc=str(row["source_as_of_utc"]),
                available_at_utc=str(row["available_at_utc"]),
                bundle=bundle,
            )
        )
    return tuple(observations)


def _parse_window(value: str) -> StressWindow:
    parts = value.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("stress window must be ID:YYYY-MM-DD:YYYY-MM-DD")
    return StressWindow(parts[0], parts[1], parts[2])


def _atomic_json_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(raw)
        handle.flush()
    try:
        temp_path.replace(path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare baseline weights with a shadow-only Leningrad cascade gross cap. "
            "No security selection, entry/exit, or capital authority is changed."
        )
    )
    parser.add_argument("--weights-csv", required=True, type=Path)
    parser.add_argument("--returns-csv", required=True, type=Path)
    parser.add_argument("--observations-json", required=True, type=Path)
    parser.add_argument(
        "--stress-window",
        required=True,
        action="append",
        type=_parse_window,
        help="Repeat as ID:YYYY-MM-DD:YYYY-MM-DD; windows must not overlap.",
    )
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--cost-rate", type=float, default=0.0010)
    parser.add_argument("--watch-gross-cap", type=float, default=0.75)
    parser.add_argument("--severe-gross-cap", type=float, default=0.50)
    parser.add_argument("--min-mdd-improvement", type=float, default=0.15)
    parser.add_argument("--min-es-improvement", type=float, default=0.10)
    parser.add_argument("--max-alpha-drag", type=float, default=0.01)
    parser.add_argument("--max-turnover-increase", type=float, default=0.20)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    weights = _load_matrix(args.weights_csv)
    returns = _load_matrix(args.returns_csv)
    observations = _load_observations(args.observations_json)
    policy = FinancialCascadePolicy(
        watch_gross_cap=float(args.watch_gross_cap),
        severe_gross_cap=float(args.severe_gross_cap),
    )
    thresholds = CascadePromotionThresholds(
        min_relative_max_drawdown_improvement=float(args.min_mdd_improvement),
        min_expected_shortfall_improvement=float(args.min_es_improvement),
        max_annualized_net_alpha_drag=float(args.max_alpha_drag),
        max_relative_turnover_increase=float(args.max_turnover_increase),
    )
    report = run_financial_cascade_shadow(
        target_weights=weights,
        returns_df=returns,
        observations=observations,
        stress_windows=tuple(args.stress_window),
        cost_rate=float(args.cost_rate),
        policy=policy,
        thresholds=thresholds,
    )
    report["inputs"] = {
        "weights_csv_sha256": _sha256_file(args.weights_csv),
        "returns_csv_sha256": _sha256_file(args.returns_csv),
        "observations_json_sha256": _sha256_file(args.observations_json),
    }
    execution_preimage = json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    report["execution_identity"] = sha256(execution_preimage).hexdigest()
    _atomic_json_write(args.output_json, report)
    print(
        json.dumps(
            {
                "status": "complete",
                "decision": report["decision"],
                "report_identity": report["report_identity"],
                "execution_identity": report["execution_identity"],
                "output": str(args.output_json),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
