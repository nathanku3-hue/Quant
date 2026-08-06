"""Machine-checkable zero-compatibility acceptance scan for the AOV authority path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def scan_zero_compat() -> dict[str, int]:
    dashboard = _text("dashboard.py")
    adapter = _text("research/adapters/rule100_replay_adapter.py")
    book = _text("gv_portfolio_v0/book.py")
    runner = _text("research/backtest_runner.py")
    evidence = _text("research/evidence_schema.py")

    root_duplicates = sum(
        (ROOT / name).exists()
        for name in ("alpha_app.py", "launch_alpha.py", "portfolio_app.py", "launch_portfolio.py")
    )
    ticker_asset_aliases = sum(
        token in adapter
        for token in (
            "_resolve_asset_column",
            "fallback in (\"asset\", \"ticker\")",
            "asset_column:",
        )
    )
    legacy_book_projection = int("def reduce_events(" in book)
    transitional_authority_fallback = sum(
        token in dashboard
        for token in (
            "_defer_legacy_page",
            "transitional_build",
            "_render_legacy_backtest_table",
            "_render_portfolio_builder_placeholder",
            "render_optimizer_view",
            "import yfinance",
        )
    )
    mutable_evidence_manifest_bypass = sum(
        token in evidence
        for token in (
            "_clear_previous_final_manifest",
            "exist_ok=True",
        )
    ) + int("evidence_manifest.json" not in evidence)
    unnamed_benchmark_selection = sum(
        token in runner
        for token in (
            "next(iter(benchmark_results.values())",
            "first_benchmark_result",
        )
    )
    return {
        "root_duplicate_app_count": int(root_duplicates),
        "aov_ticker_asset_fallback_count": int(ticker_asset_aliases),
        "aov_legacy_book_projection_count": int(legacy_book_projection),
        "aov_transitional_authority_fallback_count": int(transitional_authority_fallback),
        "mutable_evidence_manifest_bypass_count": int(mutable_evidence_manifest_bypass),
        "unnamed_benchmark_selection_count": int(unnamed_benchmark_selection),
    }


def main() -> int:
    result = scan_zero_compat()
    print(json.dumps(result, sort_keys=True))
    return 0 if all(value == 0 for value in result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
