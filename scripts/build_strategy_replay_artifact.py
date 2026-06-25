"""Build display-only PIT replay input artifacts from local parquet matrices."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data_orchestrator import load_strategy_replay_inputs
from core.data_orchestrator import write_strategy_replay_artifact_atomic
from core.data_orchestrator import load_batched_pit_replay_data
from core.data_orchestrator import build_batched_pit_input_loader
from core.data_orchestrator import load_replay_date_index
from strategies.strategy_replay import ReplayBudgetPolicy
from strategies.strategy_replay import build_selected_method_replay_with_budget
from strategies.strategy_replay import write_selected_method_replay_artifact_atomic
from strategies.strategy_replay import _compute_coverage_plan
from strategies.optimizer import OptimizationMethod


def _parse_controls(raw: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --controls-json: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--controls-json must decode to an object")
    return parsed


def _load_rule100_candidates(path: str | None) -> pd.DataFrame | None:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    if p.suffix == ".csv":
        return pd.read_csv(p)
    return pd.read_parquet(p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a local display-only strategy replay input artifact."
    )
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--method", default="portfolio_replay")
    parser.add_argument("--max-weight", type=float, default=0.35)
    parser.add_argument("--controls-json", default="{}")
    parser.add_argument("--top-n", type=int, default=2000)
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--universe-mode", default="r3000_pit")
    parser.add_argument("--processed-dir", default="./data/processed")
    parser.add_argument("--static-dir", default="./data/static")
    parser.add_argument("--cache-dir", default="data/runtime_cache/strategy_replay")
    parser.add_argument("--output-path", default=None)
    parser.add_argument(
        "--artifact-kind",
        choices=("input", "selected-method-output"),
        default="input",
        help="Build either a PIT input artifact or a selected-method replay output artifact.",
    )
    parser.add_argument("--lookback-years", type=int, default=5)
    parser.add_argument("--rule100-candidate-path", default=None)
    parser.add_argument("--budget-max-seconds", type=int, default=300)
    parser.add_argument("--budget-max-rows", type=int, default=500_000)
    parser.add_argument("--budget-max-dates", type=int, default=2_000)
    parser.add_argument("--budget-max-elapsed-ms", type=float, default=300_000.0)
    parser.add_argument("--max-membership-gap-days", type=int, default=30)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    controls = _parse_controls(args.controls_json)
    controls.setdefault("max_weight", args.max_weight)

    if args.start_date is None:
        as_of_ts = pd.Timestamp(args.as_of_date)
        start_ts = as_of_ts - pd.DateOffset(years=args.lookback_years)
        replay_start = start_ts.strftime("%Y-%m-%d")
    else:
        replay_start = args.start_date
    replay_end = args.end_date or args.as_of_date

    rule100_candidates = _load_rule100_candidates(args.rule100_candidate_path)
    if rule100_candidates is not None:
        controls["rule100_candidate_frame"] = rule100_candidates

    if args.artifact_kind == "selected-method-output":
        wall_start = time.time()

        trading_dates = load_replay_date_index(
            processed_dir=args.processed_dir,
            start_date=replay_start,
            end_date=replay_end,
        )

        batched = load_batched_pit_replay_data(
            processed_dir=args.processed_dir,
            static_dir=args.static_dir,
            start_date=replay_start,
            end_date=replay_end,
            start_year=args.start_year,
        )

        input_loader = build_batched_pit_input_loader(
            batched,
            max_membership_gap_days=args.max_membership_gap_days,
        )

        try:
            method_enum = OptimizationMethod(args.method)
        except ValueError:
            method_enum = OptimizationMethod.INVERSE_VOLATILITY

        coverage_plan = _compute_coverage_plan(
            method=method_enum,
            controls=controls,
            replay_dates=trading_dates,
            batched=batched,
            max_membership_gap_days=args.max_membership_gap_days,
        )

        elapsed = time.time() - wall_start
        if elapsed > args.budget_max_seconds:
            print(f"BUDGET_EXCEEDED: {elapsed:.1f}s > {args.budget_max_seconds}s", file=sys.stderr)
            return 1

        budget_policy = ReplayBudgetPolicy(
            cold_start_max_seconds=float(args.budget_max_seconds),
            rerun_cache_max_seconds=2.0,
            max_rows=int(args.budget_max_rows),
            max_dates=int(args.budget_max_dates),
            max_elapsed_ms=float(args.budget_max_elapsed_ms),
        )
        replay_result = build_selected_method_replay_with_budget(
            method=args.method,
            controls=controls,
            prices=None,
            ticker_map=None,
            sector_map=None,
            as_of_range=trading_dates,
            input_loader=input_loader,
            start_date=replay_start,
            end_date=replay_end,
            coverage_plan=coverage_plan,
            budget_policy=budget_policy,
        )
        if not replay_result.available or replay_result.bundle is None:
            print(f"REPLAY_UNAVAILABLE: {replay_result.reason}", file=sys.stderr)
            return 1
        bundle = replay_result.bundle

        elapsed = time.time() - wall_start
        if elapsed > args.budget_max_seconds:
            print(f"BUDGET_EXCEEDED: {elapsed:.1f}s > {args.budget_max_seconds}s", file=sys.stderr)
            return 1

        result = write_selected_method_replay_artifact_atomic(
            bundle,
            artifact_path=args.output_path,
            cache_dir=args.cache_dir,
        )
        elapsed = time.time() - wall_start
        if elapsed > args.budget_max_seconds:
            for key in ("artifact_path", "manifest_path"):
                path_value = result.get(key)
                if path_value:
                    Path(path_value).unlink(missing_ok=True)
            print(f"BUDGET_EXCEEDED: {elapsed:.1f}s > {args.budget_max_seconds}s", file=sys.stderr)
            return 1
        print(f"run_id={result['run_id']}")
        print(f"source_id={result['source_id']}")
        print(f"artifact_path={result['artifact_path']}")
        print(f"manifest_path={result['manifest_path']}")
        print(f"row_counts={json.dumps(bundle.run_metadata.row_counts, sort_keys=True)}")
        print(f"status_counts={json.dumps(bundle.run_metadata.status_counts, sort_keys=True)}")
        print(f"timing={json.dumps(bundle.run_metadata.timing, sort_keys=True)}")
        print(f"elapsed_wall_seconds={elapsed:.1f}")
        return 0

    inputs = load_strategy_replay_inputs(
        as_of_date=args.as_of_date,
        start_date=args.start_date,
        end_date=args.end_date,
        method=args.method,
        controls=controls,
        max_weight=args.max_weight,
        top_n=args.top_n,
        start_year=args.start_year,
        universe_mode=args.universe_mode,
        processed_dir=args.processed_dir,
        static_dir=args.static_dir,
    )
    result = write_strategy_replay_artifact_atomic(
        inputs,
        artifact_path=args.output_path,
        cache_dir=args.cache_dir,
    )
    print(f"cache_key={result['cache_key']}")
    print(f"artifact_path={result['artifact_path']}")
    print(f"manifest_path={result['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
