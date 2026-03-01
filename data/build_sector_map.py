"""
Terminal Zero — Sector/Industry Map Builder (Phase 7 foundation)

One-off / occasional metadata job:
  - Fetch sector + industry for a target universe from Yahoo.
  - Save to data/static/sector_map.parquet.
  - Supports resume to avoid re-fetching completed tickers.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
STATIC_DIR = os.path.join(PROJECT_ROOT, "data", "static")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
OUTPUT_PATH = os.path.join(STATIC_DIR, "sector_map.parquet")

UNKNOWN = "Unknown"


def _normalize_tickers(values) -> list[str]:
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip().upper()
        if s:
            out.append(s)
    return list(dict.fromkeys(out))


def _resolve_universe(scope: str, custom_tickers: str | None) -> list[str]:
    if custom_tickers:
        return _normalize_tickers(custom_tickers.split(","))

    if scope.lower() == "all":
        if not os.path.exists(TICKERS_PATH):
            return []
        tickers_df = pd.read_parquet(TICKERS_PATH, columns=["ticker"])
        return _normalize_tickers(tickers_df["ticker"].tolist())

    n = 2000
    scope_upper = str(scope).upper()
    if "3000" in scope_upper:
        n = 3000
    elif "2000" in scope_upper:
        n = 2000
    elif "500" in scope_upper:
        n = 500
    elif "200" in scope_upper:
        n = 200
    elif "100" in scope_upper:
        n = 100
    elif "50" in scope_upper:
        n = 50
    return _normalize_tickers(updater.get_top_liquid_tickers(n))


def _safe_get_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def _classify_sector_industry(info: dict) -> tuple[str, str, str]:
    quote_type = str(info.get("quoteType", UNKNOWN)).upper() if info else UNKNOWN
    sector = str(info.get("sector", UNKNOWN)).strip() if info else UNKNOWN
    industry = str(info.get("industry", UNKNOWN)).strip() if info else UNKNOWN

    if not sector:
        sector = UNKNOWN
    if not industry:
        industry = UNKNOWN

    if quote_type == "ETF":
        sector = "ETF"
        if industry == UNKNOWN:
            industry = "Exchange Traded Fund"
    elif quote_type in {"MUTUALFUND", "INDEX", "CRYPTOCURRENCY"} and sector == UNKNOWN:
        sector = quote_type.title()
        if industry == UNKNOWN:
            industry = quote_type.title()

    return sector, industry, quote_type


def _atomic_write(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _load_existing(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["ticker", "permno", "sector", "industry", "quote_type", "source", "updated_at"])
    try:
        df = pd.read_parquet(path)
        if df.empty:
            return pd.DataFrame(columns=["ticker", "permno", "sector", "industry", "quote_type", "source", "updated_at"])
        for c in ["ticker", "sector", "industry", "quote_type", "source"]:
            if c not in df.columns:
                df[c] = UNKNOWN
        if "permno" not in df.columns:
            df["permno"] = pd.NA
        if "updated_at" not in df.columns:
            df["updated_at"] = pd.NaT
        df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
        df = df.dropna(subset=["ticker"])
        return df
    except Exception:
        return pd.DataFrame(columns=["ticker", "permno", "sector", "industry", "quote_type", "source", "updated_at"])


def build_sector_map(
    scope: str = "Top 2000",
    custom_tickers: str | None = None,
    output_path: str = OUTPUT_PATH,
    sleep_sec: float = 0.15,
    checkpoint_every: int = 50,
    force_refresh: bool = False,
):
    print("=" * 62)
    print(f"🗺️  Building Sector Map — Scope: {scope}")
    print("=" * 62)

    if not os.path.exists(TICKERS_PATH):
        print("✗ Missing tickers.parquet. Run ETL/updater first.")
        return 1

    targets = _resolve_universe(scope=scope, custom_tickers=custom_tickers)
    if not targets:
        print("✗ No target tickers found.")
        return 1

    tickers_df = pd.read_parquet(TICKERS_PATH, columns=["permno", "ticker"])
    tickers_df["ticker"] = tickers_df["ticker"].astype(str).str.upper().str.strip()
    tickers_df["permno"] = pd.to_numeric(tickers_df["permno"], errors="coerce").astype("Int64")
    t2p = dict(zip(tickers_df["ticker"], tickers_df["permno"]))

    existing = _load_existing(output_path)
    done = set()
    if not force_refresh and not existing.empty:
        ok = existing["sector"].fillna(UNKNOWN).ne(UNKNOWN) | existing["industry"].fillna(UNKNOWN).ne(UNKNOWN)
        done = set(existing.loc[ok, "ticker"].tolist())

    queue = [t for t in targets if force_refresh or t not in done]
    print(f"🎯 Targets: {len(targets)} | To Fetch: {len(queue)} | Reused: {len(targets) - len(queue)}")

    rows = []
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for i, ticker in enumerate(queue, start=1):
        info = _safe_get_info(ticker)
        sector, industry, quote_type = _classify_sector_industry(info)
        rows.append(
            {
                "ticker": ticker,
                "permno": t2p.get(ticker),
                "sector": sector or UNKNOWN,
                "industry": industry or UNKNOWN,
                "quote_type": quote_type or UNKNOWN,
                "source": "yfinance",
                "updated_at": ts,
            }
        )

        if i % checkpoint_every == 0 or i == len(queue):
            print(f"   Processed {i}/{len(queue)}")
            combined = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
            combined["ticker"] = combined["ticker"].astype(str).str.upper().str.strip()
            combined = combined.sort_values(["ticker", "updated_at"]).drop_duplicates(subset=["ticker"], keep="last")
            # Keep only the requested universe to avoid uncontrolled growth.
            combined = combined[combined["ticker"].isin(targets)]
            _atomic_write(combined, output_path)
            existing = combined
            rows.clear()

        if sleep_sec > 0:
            time.sleep(sleep_sec)

    final_df = _load_existing(output_path)
    if final_df.empty:
        print("✗ Build failed: output is empty.")
        return 1

    # Ensure permno is populated from latest map where possible.
    final_df["permno"] = final_df["permno"].fillna(final_df["ticker"].map(t2p))
    final_df = final_df.sort_values("ticker").reset_index(drop=True)
    _atomic_write(final_df, output_path)

    print(f"✅ Saved: {output_path}")
    print(f"📦 Rows: {len(final_df)}")
    print("📊 Top sectors:")
    print(final_df["sector"].fillna(UNKNOWN).value_counts().head(10).to_string())
    print("=" * 62)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Build Sector/Industry map for Terminal Zero universe.")
    parser.add_argument(
        "--scope",
        default="Top 2000",
        help="'Top 50', 'Top 100', 'Top 200', 'Top 500', 'Top 2000', 'Top 3000', or 'All'",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated ticker list (overrides --scope)",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_PATH,
        help="Output parquet path",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Delay between Yahoo calls (seconds)",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=50,
        help="Checkpoint write frequency",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Refetch all targets even if already present in output",
    )
    args = parser.parse_args()

    code = build_sector_map(
        scope=args.scope,
        custom_tickers=args.tickers,
        output_path=args.output,
        sleep_sec=args.sleep,
        checkpoint_every=max(1, int(args.checkpoint_every)),
        force_refresh=bool(args.force_refresh),
    )
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
