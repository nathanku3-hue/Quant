from __future__ import annotations

from pathlib import Path


YFINANCE_DIRECT_USE_ALLOWLIST = frozenset(
    {
        "dashboard.py",
        "data/build_sector_map.py",
        "data/calendar_updater.py",
        "data/fundamentals_updater.py",
        "data/liquidity_loader.py",
        "data/macro_loader.py",
        "data/updater.py",
        "data/providers/legacy_allowlist.py",
        "data/providers/yahoo_provider.py",
        "execution/alpha_sniper.py",
        "scripts/align_osiris_macro.py",
        "scripts/alpha_lead_backtest.py",
        "scripts/alpha_quad_scanner.py",
        "scripts/asset_classifier.py",
        "scripts/asset_elasticity_calibration.py",
        "scripts/atr_backtest.py",
        "scripts/black_swan_survival.py",
        "scripts/breadth_backtest.py",
        "scripts/check_user_tickers.py",
        "scripts/convex_alpha_scanner.py",
        "scripts/crash_autopsy.py",
        "scripts/derivative_backtest.py",
        "scripts/derivative_macro_backtest.py",
        "scripts/diagnose_msft.py",
        "scripts/diagnose_super_cycle.py",
        "scripts/elite_sniper_backtest.py",
        "scripts/fourier_opportunity_gate.py",
        "scripts/high_freq_data.py",
        "scripts/infinite_sniper_backtest.py",
        "scripts/kinetic_cluster_backtest.py",
        "scripts/kinetic_vs_static_backtest.py",
        "scripts/macro_score_calibration.py",
        "scripts/macro_stress_test.py",
        "scripts/macro_stress_test_v2.py",
        "scripts/measure_wick_depth.py",
        "scripts/nonlinear_sniper_backtest.py",
        "scripts/optimize_composite_weights.py",
        "scripts/optimize_execution_lanes.py",
        "scripts/options_hedging.py",
        "scripts/orbis_signal_generator.py",
        "scripts/osiris_fire_ice_backtest.py",
        "scripts/osiris_regime_backtest.py",
        "scripts/osiris_rotation_backtest.py",
        "scripts/osiris_term_structure.py",
        "scripts/phase_reversal_monitor.py",
        "scripts/proxy_validation.py",
        "scripts/rule_100_backtest_1990_2000.py",
        "scripts/rule_100_backtest_2010_2020.py",
        "scripts/rule_100_backtest_decades.py",
        "scripts/scout_drone.py",
        "scripts/smart_entry_backtest.py",
        "scripts/sovereign_oscillator_backtest.py",
        "scripts/strong_buy_scan.py",
        "scripts/super_cycle_scanner.py",
        "scripts/test_visual.py",
        "scripts/tighten_vs_sell_backtest.py",
        "scripts/train_neuro_gate.py",
        "scripts/universal_cluster_audit.py",
    }
)

SCAN_ROOTS = (
    "core",
    "data",
    "execution",
    "scripts",
    "strategies",
    "views",
)
SKIP_PREFIXES = (
    ".venv/",
    "data/processed/",
    "data/raw/",
    "docs/",
    "research_data/",
)


def normalize_repo_path(path: str | Path, repo_root: str | Path) -> str:
    return Path(path).resolve().relative_to(Path(repo_root).resolve()).as_posix()


def scan_direct_yfinance_uses(repo_root: str | Path) -> list[str]:
    root = Path(repo_root)
    matches: list[str] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
                continue
            if "__pycache__" in rel:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "import yfinance" in text or "yf." in text:
                matches.append(rel)
    for path in (root / "dashboard.py",):
        if not path.exists():
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "import yfinance" in text or "yf." in text:
            matches.append(rel)
    return sorted(matches)
