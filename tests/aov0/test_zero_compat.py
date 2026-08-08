from __future__ import annotations

from scripts.aov_zero_compat_scan import scan_zero_compat


def test_aov_zero_compat_scan_is_all_zero() -> None:
    assert scan_zero_compat() == {
        "root_duplicate_app_count": 0,
        "aov_ticker_asset_fallback_count": 0,
        "aov_legacy_book_projection_count": 0,
        "aov_transitional_authority_fallback_count": 0,
        "mutable_evidence_manifest_bypass_count": 0,
        "unnamed_benchmark_selection_count": 0,
        "archived_executable_source_import_count": 0,
    }
