"""
Terminal Zero — Auto-Update Script [FR-025]

Standalone script that reads the Smart Watchlist (data/watchlist.json)
and batch-downloads fresh data from Yahoo Finance.

Usage:
    python data/auto_update.py             # Run manually
    python data/auto_update.py --dry-run   # Preview tickers without downloading

Can be scheduled via Windows Task Scheduler for daily pre-market updates.
"""

import json
import os
import sys

# Add project root to path so we can import the updater module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import updater

WATCHLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.json")


def load_watchlist() -> list[str]:
    """Read watchlist.json → deduplicated ticker list."""
    if not os.path.exists(WATCHLIST_PATH):
        print(f"⚠️  Watchlist not found at {WATCHLIST_PATH}, using defaults.")
        return ["AAPL", "MSFT", "SPY"]
    with open(WATCHLIST_PATH, "r") as f:
        data = json.load(f)
    full_list = list(set(data.get("defaults", []) + data.get("user_added", [])))
    full_list.sort()
    return full_list


def run_auto_update(dry_run: bool = False):
    """Main entry point: load watchlist → call updater → report."""
    print("=" * 60)
    print("⏰ Terminal Zero — Auto-Update Routine")
    print("=" * 60)

    # 1. Read Smart Watchlist
    targets = load_watchlist()
    print(f"📋 Watchlist ({len(targets)} tickers): {', '.join(targets)}")

    if dry_run:
        print("\n🔍 DRY RUN — no data downloaded.")
        return

    # 2. Run Updater with Custom scope
    custom_str = ",".join(targets)
    result = updater.run_update(scope="Custom", custom_list=custom_str)

    # 3. Report
    print()
    if result["success"]:
        print(f"✅ Success! Updated {result['tickers_updated']} tickers → {result['last_date']}")
    else:
        print("❌ Update Failed. Logs:")
        for line in result["log"]:
            print(f"  {line}")

    return result


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run_auto_update(dry_run=dry)
