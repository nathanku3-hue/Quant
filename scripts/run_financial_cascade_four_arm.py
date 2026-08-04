"""Run the cascade four-arm attribution on Quant's existing G5 portfolio."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.financial_cascade_four_arm import (  # noqa: E402
    ENGINEERING_ONLY,
    GOVERNED_PIT,
    REMAIN_REDUCED,
    RESTORE_FROZEN_BASELINE_TARGET,
    CascadeExperimentExitRule,
    GovernedCascadeEvidence,
    load_existing_g5_nonzero_portfolio,
    run_financial_cascade_four_arm,
)
from strategies.financial_cascade import (  # noqa: E402
    FinancialCascadeObservation,
    FinancialCascadePolicy,
    load_verified_leningrad_bundle,
)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CASCADE_FOUR_ARM_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def _parse_regime_step(value: str) -> tuple[pd.Timestamp, float]:
    try:
        date_text, scalar_text = value.split(":", 1)
        date = pd.Timestamp(date_text)
        scalar = float(scalar_text)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            "regime step must be YYYY-MM-DD:SCALAR"
        ) from exc
    if date.tzinfo is not None or date != date.normalize():
        raise argparse.ArgumentTypeError("regime step date must be a naive date")
    if not 0.0 <= scalar <= 1.5:
        raise argparse.ArgumentTypeError("regime scalar must be in [0, 1.5]")
    return date, scalar


def _macro_from_steps(
    index: pd.DatetimeIndex, steps: Sequence[tuple[pd.Timestamp, float]]
) -> pd.DataFrame:
    if not steps:
        raise ValueError("CASCADE_FOUR_ARM_REGIME_STEP_REQUIRED")
    ordered = sorted(steps, key=lambda row: row[0])
    if len({date for date, _ in ordered}) != len(ordered):
        raise ValueError("CASCADE_FOUR_ARM_DUPLICATE_REGIME_STEP_DATE")
    if ordered[0][0] > index[0]:
        raise ValueError("CASCADE_FOUR_ARM_FIRST_REGIME_STEP_MUST_COVER_PORTFOLIO_START")
    values = pd.Series(index=index, dtype=float)
    for date, scalar in ordered:
        if date not in index:
            raise ValueError("CASCADE_FOUR_ARM_REGIME_STEP_NOT_IN_PORTFOLIO_CALENDAR")
        values.loc[date] = scalar
    return pd.DataFrame({"regime_scalar": values.ffill()}, index=index)


def _load_governed_proof(
    path: Path | None,
    *,
    bundle_identity: str,
) -> dict[str, GovernedCascadeEvidence] | None:
    if path is None:
        return None
    raw = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_strict_object,
    )
    required = {
        "institutional_network_source_identity",
        "liabilities_source_identity",
        "shock_source_identity",
        "source_as_of_utc",
        "available_at_utc",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise ValueError("CASCADE_GOVERNED_PROOF_FIELDS_INVALID")
    return {
        bundle_identity: GovernedCascadeEvidence(
            institutional_network_source_identity=str(
                raw["institutional_network_source_identity"]
            ),
            liabilities_source_identity=str(raw["liabilities_source_identity"]),
            shock_source_identity=str(raw["shock_source_identity"]),
            source_as_of_utc=str(raw["source_as_of_utc"]),
            available_at_utc=str(raw["available_at_utc"]),
        )
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run baseline, existing-regime, cascade-only, and combined arms on "
            "Quant's existing G5 nonzero canonical portfolio."
        )
    )
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--bundle-identity", required=True)
    parser.add_argument("--source-as-of-utc", required=True)
    parser.add_argument("--available-at-utc", required=True)
    parser.add_argument("--effective-date", required=True)
    parser.add_argument(
        "--regime-step",
        required=True,
        action="append",
        type=_parse_regime_step,
        help="Repeat as YYYY-MM-DD:SCALAR; consumed by the existing RegimeManager.",
    )
    parser.add_argument("--evaluation-horizon-end", required=True)
    parser.add_argument("--maximum-holding-sessions", required=True, type=int)
    parser.add_argument("--manual-review-date", required=True)
    parser.add_argument(
        "--terminal-disposition",
        required=True,
        choices=[RESTORE_FROZEN_BASELINE_TARGET, REMAIN_REDUCED],
    )
    parser.add_argument("--reconciliation-date", required=True)
    parser.add_argument(
        "--evidence-classification",
        choices=[ENGINEERING_ONLY, GOVERNED_PIT],
        default=ENGINEERING_ONLY,
    )
    parser.add_argument("--governed-proof-json", type=Path)
    parser.add_argument("--watch-gross-cap", type=float, default=0.75)
    parser.add_argument("--severe-gross-cap", type=float, default=0.50)
    parser.add_argument("--cost-rate", type=float, default=0.0010)
    parser.add_argument("--output-json", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    portfolio = load_existing_g5_nonzero_portfolio(repo_root=REPO_ROOT)
    macro = _macro_from_steps(
        pd.DatetimeIndex(portfolio.target_weights.index),
        tuple(args.regime_step),
    )
    bundle = load_verified_leningrad_bundle(
        args.bundle_dir,
        expected_bundle_identity=str(args.bundle_identity),
    )
    observation = FinancialCascadeObservation(
        effective_date=str(args.effective_date),
        source_as_of_utc=str(args.source_as_of_utc),
        available_at_utc=str(args.available_at_utc),
        bundle=bundle,
    )
    exit_rule = CascadeExperimentExitRule(
        overlay_effective_date=str(args.effective_date),
        evaluation_horizon_end_date=str(args.evaluation_horizon_end),
        maximum_holding_period_sessions=int(args.maximum_holding_sessions),
        manual_review_date=str(args.manual_review_date),
        terminal_disposition=str(args.terminal_disposition),
        reconciliation_date=str(args.reconciliation_date),
    )
    governed = _load_governed_proof(
        args.governed_proof_json,
        bundle_identity=bundle.bundle_identity,
    )
    report = run_financial_cascade_four_arm(
        target_weights=portfolio.target_weights,
        returns_df=portfolio.returns_df,
        macro_df=macro,
        observations=(observation,),
        exit_rule=exit_rule,
        portfolio_source_identity=portfolio.source_identity,
        evidence_classification=str(args.evidence_classification),
        governed_evidence_by_bundle=governed,
        cost_rate=float(args.cost_rate),
        policy=FinancialCascadePolicy(
            watch_gross_cap=float(args.watch_gross_cap),
            severe_gross_cap=float(args.severe_gross_cap),
        ),
    )
    report["cli_inputs"] = {
        "bundle_index_sha256": _sha256_file(args.bundle_dir / "bundle_index.json"),
        "scenario_sha256": _sha256_file(args.bundle_dir / "scenario.json"),
        "comparison_sha256": _sha256_file(args.bundle_dir / "comparison.json"),
        "report_sha256": _sha256_file(args.bundle_dir / "report.md"),
        "governed_proof_sha256": (
            _sha256_file(args.governed_proof_json)
            if args.governed_proof_json is not None
            else None
        ),
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
                "evidence_classification": report["evidence_classification"],
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
