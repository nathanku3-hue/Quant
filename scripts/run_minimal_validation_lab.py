from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data.provenance import ManifestInput  # noqa: E402
from data.provenance import SOURCE_QUALITY_CANONICAL  # noqa: E402
from data.provenance import build_manifest  # noqa: E402
from data.provenance import load_manifest  # noqa: E402
from data.provenance import manifest_path_for  # noqa: E402
from data.provenance import write_json_atomic  # noqa: E402
from data.provenance import write_manifest  # noqa: E402
from validation.schemas import run_minimal_validation_lab  # noqa: E402

DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "phase56_pead_evidence.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "minimal_validation_report.json"


def _load_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal validation lab on a return stream.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--input-manifest", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--return-col", default="net_ret")
    parser.add_argument("--strategy-id", default="PHASE56_PEAD_CAPITAL_CYCLE_V1")
    parser.add_argument("--promotion-intent", action="store_true")
    parser.add_argument("--create-input-manifest", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    frame = _load_frame(input_path)

    manifest_path = Path(args.input_manifest) if args.input_manifest else manifest_path_for(input_path)
    if args.create_input_manifest:
        date_range = {"start": None, "end": None}
        if "date" in frame.columns:
            dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
            if not dates.empty:
                date_range = {"start": str(dates.min().date()), "end": str(dates.max().date())}
        manifest = build_manifest(
            ManifestInput(
                artifact_path=input_path,
                source_quality=SOURCE_QUALITY_CANONICAL,
                provider="terminal_zero",
                provider_feed="v1_engine_evidence",
                license_scope="internal_research_validation",
                row_count=int(len(frame)),
                date_range=date_range,
                schema_version="1.0.0",
            )
        )
        write_manifest(manifest, manifest_path)
    manifest = load_manifest(manifest_path)
    report = run_minimal_validation_lab(
        frame,
        source_manifest=manifest,
        strategy_id=str(args.strategy_id),
        return_col=str(args.return_col),
        promotion_intent=bool(args.promotion_intent),
    ).to_dict()
    write_json_atomic(report, output_path)
    report_manifest = build_manifest(
        ManifestInput(
            artifact_path=output_path,
            source_quality=SOURCE_QUALITY_CANONICAL,
            provider="terminal_zero",
            provider_feed="minimal_validation_lab",
            license_scope="internal_research_validation",
            row_count=1,
            date_range={"start": report["generated_at_utc"], "end": report["generated_at_utc"]},
            schema_version=str(report.get("schema_version") or "1.0.0"),
        )
    )
    report_manifest_path = write_manifest(report_manifest, artifact_path=output_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Report: {output_path}")
    print(f"Manifest: {report_manifest_path}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

