"""
Institutional Factor Layer Validation (FR-033)

Checks:
  1) PIT integrity on canonical quarterly rows.
  2) Cash-flow de-cumulation correctness.
  3) Q4 spike sanity.
  4) Debt fallback robustness and EV/EBITDA arithmetic consistency.
  5) Snapshot factor coverage for live scanner usage.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

FUND_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "fundamentals.parquet")
SNAP_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "fundamentals_snapshot.parquet")

REQUIRED_FUND_COLS = {
    "permno",
    "fiscal_period_end",
    "release_date",
    "fyearq",
    "fqtr",
    "net_income_q",
    "equity_q",
    "cogs_q",
    "receivables_q",
    "deferred_revenue_q",
    "book_to_bill_proxy_q",
    "gm_accel_q",
    "delta_dso_q",
    "eps_q",
    "eps_growth_yoy",
    "roe_q",
    "oancfy",
    "oancf_q",
    "oibdpq",
    "ebitda_ttm",
    "dlttq",
    "dlcq",
    "total_debt",
    "ev",
    "ev_ebitda",
    "source",
    "ingested_at",
}
REQUIRED_SNAP_COLS = {
    "quality_pass",
    "book_to_bill_proxy_q",
    "gm_accel_q",
    "delta_dso_q",
    "roe_q",
    "eps_q",
    "eps_growth_yoy",
    "ev_ebitda",
    "leverage_ratio",
    "rd_intensity",
    "oancf_ttm",
    "ebitda_ttm",
}


def _fail(msg: str) -> bool:
    print(f"✗ {msg}")
    return False


def validate() -> bool:
    print("Starting Institutional Factor Layer Validation...")
    if not os.path.exists(FUND_PATH):
        return _fail(f"missing {FUND_PATH}")
    if not os.path.exists(SNAP_PATH):
        return _fail(f"missing {SNAP_PATH}")

    fund = pd.read_parquet(FUND_PATH)
    snap = pd.read_parquet(SNAP_PATH)

    miss_fund = sorted(REQUIRED_FUND_COLS - set(fund.columns))
    miss_snap = sorted(REQUIRED_SNAP_COLS - set(snap.columns))
    if miss_fund:
        return _fail(f"fundamentals schema missing columns: {miss_fund}")
    if miss_snap:
        return _fail(f"snapshot schema missing columns: {miss_snap}")

    fund = fund.copy()
    fund["fiscal_period_end"] = pd.to_datetime(fund["fiscal_period_end"], errors="coerce")
    fund["release_date"] = pd.to_datetime(fund["release_date"], errors="coerce")
    fund["ingested_at"] = pd.to_datetime(fund["ingested_at"], errors="coerce")
    fund["fyearq"] = pd.to_numeric(fund["fyearq"], errors="coerce")
    fund["fqtr"] = pd.to_numeric(fund["fqtr"], errors="coerce")
    for c in [
        "net_income_q",
        "equity_q",
        "eps_q",
        "eps_growth_yoy",
        "roe_q",
        "book_to_bill_proxy_q",
        "gm_accel_q",
        "delta_dso_q",
        "oancfy",
        "oancf_q",
        "oibdpq",
        "ebitda_ttm",
        "dlttq",
        "dlcq",
        "total_debt",
        "ev",
        "ev_ebitda",
    ]:
        fund[c] = pd.to_numeric(fund[c], errors="coerce")

    # Source-precedence dedupe per fiscal period.
    pri = {"yfinance": 0, "compustat_csv": 1}
    fund["_pri"] = fund["source"].map(pri).fillna(0)
    q = fund.sort_values(["permno", "fiscal_period_end", "_pri", "ingested_at"]).drop_duplicates(
        ["permno", "fiscal_period_end"], keep="last"
    )

    print(f"Rows (dedup fiscal): {len(q):,}")

    # 1) PIT integrity
    pit_bad = q[
        q["fiscal_period_end"].notna()
        & q["release_date"].notna()
        & (q["release_date"] <= q["fiscal_period_end"])
    ]
    print(f"PIT violations: {len(pit_bad):,}")

    # 2) Decumulation check
    q = q.sort_values(["permno", "fyearq", "fqtr", "fiscal_period_end"])
    q["prev_oancfy"] = q.groupby(["permno", "fyearq"])["oancfy"].shift(1)
    mask_decum = (
        q["fqtr"].gt(1)
        & q["oancfy"].notna()
        & q["prev_oancfy"].notna()
        & q["oancf_q"].notna()
    )
    expected = q.loc[mask_decum, "oancfy"] - q.loc[mask_decum, "prev_oancfy"]
    mismatch = (q.loc[mask_decum, "oancf_q"] - expected).abs() > 1e-3
    decum_mismatch_rate = float(mismatch.mean()) if mask_decum.any() else 0.0
    print(f"Decumulation mismatch rate: {decum_mismatch_rate:.4%} ({int(mask_decum.sum()):,} comparable rows)")

    # 3) Q4 spike sanity
    ratios = []
    grouped = q[q["fqtr"].isin([1, 2, 3, 4])].groupby(["permno", "fyearq"], sort=False)
    for (_, _), g in grouped:
        q4 = g.loc[g["fqtr"] == 4, "oancf_q"]
        q123 = g.loc[g["fqtr"].isin([1, 2, 3]), "oancf_q"].abs()
        if len(q4) == 0 or q123.notna().sum() == 0:
            continue
        med = np.nanmedian(q123.values)
        if np.isnan(med) or med <= 0 or pd.isna(q4.iloc[-1]):
            continue
        ratios.append(abs(float(q4.iloc[-1])) / med)
    ratios = np.asarray(ratios, dtype=float)
    q4_spike_rate = float((ratios > 10).mean()) if ratios.size else 0.0
    q4_p95 = float(np.nanpercentile(ratios, 95)) if ratios.size else np.nan
    print(f"Q4 spike rate (>10x median Q1-Q3): {q4_spike_rate:.4%} (p95={q4_p95:.3f}, n={ratios.size:,})")

    # 4) Debt + EV consistency
    debt_missing = q["dlttq"].isna() & q["dlcq"].isna()
    debt_zero_rate = float((q.loc[debt_missing, "total_debt"] == 0).mean()) if debt_missing.any() else 1.0
    print(f"Debt fallback zero-rate when dlttq/dlcq missing: {debt_zero_rate:.4%} ({int(debt_missing.sum()):,} rows)")

    ev_mask = q["ebitda_ttm"].gt(0) & q["ev"].notna() & q["ev_ebitda"].notna()
    ev_calc = q.loc[ev_mask, "ev"] / q.loc[ev_mask, "ebitda_ttm"]
    rel_err = ((q.loc[ev_mask, "ev_ebitda"] - ev_calc).abs() / ev_calc.abs().replace(0, np.nan)).dropna()
    ev_bad_rate = float((rel_err > 0.01).mean()) if len(rel_err) else 0.0
    print(f"EV/EBITDA arithmetic bad-rate (>1% rel err): {ev_bad_rate:.4%} (n={len(rel_err):,})")

    # 5) Snapshot coverage
    snap = snap.copy()
    for c in REQUIRED_SNAP_COLS:
        snap[c] = pd.to_numeric(snap[c], errors="coerce")
    coverage = {
        c: float(1.0 - snap[c].isna().mean())
        for c in REQUIRED_SNAP_COLS
        if c != "quality_pass"
    }
    investable = snap[snap["quality_pass"].fillna(0).astype(int) == 1].copy()
    if investable.empty:
        investable = snap
    core_coverage = {c: float(1.0 - investable[c].isna().mean()) for c in ("ev_ebitda", "rd_intensity")}
    print("Snapshot factor non-null coverage:")
    for c in sorted(coverage):
        print(f"  - {c}: {coverage[c]:.2%}")
    print(
        f"Snapshot core coverage base: {len(investable):,} rows "
        f"(quality_pass==1 when available)"
    )
    for c in sorted(core_coverage):
        print(f"  - {c} (investable): {core_coverage[c]:.2%}")

    # Institutional-grade pass gates
    passed = True
    if len(pit_bad) != 0:
        print("FAIL: PIT violations detected.")
        passed = False
    if decum_mismatch_rate > 0.01:
        print("FAIL: Decumulation mismatch rate > 1%.")
        passed = False
    if q4_spike_rate > 0.05:
        print("FAIL: Q4 spike rate > 5%.")
        passed = False
    if debt_zero_rate < 0.95:
        print("FAIL: Debt fallback zero-rate < 95%.")
        passed = False
    if ev_bad_rate > 0.01:
        print("FAIL: EV/EBITDA arithmetic bad-rate > 1%.")
        passed = False
    if core_coverage["ev_ebitda"] < 0.40 or core_coverage["rd_intensity"] < 0.40:
        print("FAIL: Snapshot coverage for core valuation factors below 40%.")
        passed = False

    if passed:
        print("FACTOR LAYER: PASSED.")
    else:
        print("FACTOR LAYER: FAILED.")
    return passed


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
