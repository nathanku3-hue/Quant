from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data.phase59_shadow_portfolio import DEFAULT_DELTA_PATH  # noqa: E402
from data.phase59_shadow_portfolio import DEFAULT_EVIDENCE_PATH  # noqa: E402
from data.phase59_shadow_portfolio import DEFAULT_SUMMARY_PATH  # noqa: E402
from data.phase59_shadow_portfolio import RESEARCH_MAX_DATE  # noqa: E402
from data.phase59_shadow_portfolio import ShadowPortfolioConfig  # noqa: E402
from data.phase59_shadow_portfolio import build_phase59_packet  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402


def _to_ts(raw_value: str) -> pd.Timestamp:
    ts = pd.to_datetime(raw_value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date value: {raw_value}")
    return pd.Timestamp(ts).normalize()


def _resolve_path(raw_value: str | None, default_path: Path) -> Path:
    if raw_value is None:
        return default_path
    path = Path(raw_value)
    return path if path.is_absolute() else (PROJECT_ROOT / path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 59 bounded shadow portfolio runner.")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default="2022-12-31")
    parser.add_argument("--max-date", default=RESEARCH_MAX_DATE.date().isoformat())
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--evidence-path", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--delta-path", default=str(DEFAULT_DELTA_PATH))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = ShadowPortfolioConfig(
        start_date=_to_ts(args.start_date),
        end_date=_to_ts(args.end_date),
        max_date=_to_ts(args.max_date),
        cost_bps=float(args.cost_bps),
        summary_path=_resolve_path(args.summary_path, DEFAULT_SUMMARY_PATH),
        evidence_path=_resolve_path(args.evidence_path, DEFAULT_EVIDENCE_PATH),
        delta_path=_resolve_path(args.delta_path, DEFAULT_DELTA_PATH),
    )
    summary, evidence_frame, delta_frame = build_phase59_packet(cfg)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(evidence_frame, cfg.evidence_path)
    _atomic_csv_write(delta_frame, cfg.delta_path)

    selected_variant = summary["selected_variant"]
    shadow_reference = summary["shadow_reference"]
    print(f"Packet ID        : {summary['packet_id']}")
    print(f"Selected variant : {selected_variant['variant_id']}")
    print(f"Research Sharpe  : {selected_variant['sharpe']:.4f}")
    print(f"Research CAGR    : {selected_variant['cagr']:.4f}")
    print(f"Reference Alert  : {shadow_reference['alert_level']}")
    print(f"Holdings Overlap : {shadow_reference['holdings_overlap']:.4f}")
    print(f"Exposure Delta   : {shadow_reference['gross_exposure_delta']:.4f}")
    print(f"Turnover Delta   : {shadow_reference['turnover_delta_rel']:.4f}")
    print(f"Review Hold      : {summary['review_hold']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
