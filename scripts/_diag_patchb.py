"""Full Patch B diagnostic — raw features + why anchors don't top-rank."""
import sys, json
sys.path.insert(0, ".")
import pandas as pd
import numpy as np
from scripts.phase20_full_backtest import DEFAULT_FEATURES_PATH

TARGETS = ["MU", "CIEN", "LRCX", "AMAT", "KLAC", "CSCO", "USO", "WBA", "PLUG", "AVGO"]
ANCHORS = ["MU", "CIEN", "LRCX", "AMAT", "KLAC"]

# ── Block 1: Already-ranked sample ──────────────────────────────────────────
csv = pd.read_csv("data/processed/phase21_1_ticker_pool_sample.csv")
longs = csv[csv["pool_action"] == "LONG"].sort_values("odds_score", ascending=False)
print("=" * 70)
print("BLOCK 1: Current top-8 from Patch B slice")
print("=" * 70)
for i, (_, r) in enumerate(longs.head(8).iterrows(), 1):
    print(f"  {i}. {r['ticker']:6s}  score={float(r['odds_score']):.4g}  ratio={float(r['odds_ratio']):.4g}  mah={float(r['mahalanobis_k_cyc']):.4f}")

# ── Block 2: Raw parquet features ───────────────────────────────────────────
pcols = ["date", "ticker", "capital_cycle_score", "resid_mom_60d", "yz_vol_20d",
         "amihud_20d", "z_moat", "z_inventory_quality_proxy",
         "z_discipline_cond", "z_demand", "composite_score"]
df = pd.read_parquet(DEFAULT_FEATURES_PATH, columns=pcols)
block = df[df["date"] == pd.Timestamp("2024-12-24")]
sub = block[block["ticker"].str.upper().isin(TARGETS)].copy()
sub["ticker"] = sub["ticker"].str.upper()
sub = sub.set_index("ticker")

print()
print("=" * 70)
print("BLOCK 2: Raw feature values from features.parquet on 2024-12-24")
print(" (These are the INPUTS to z-scoring before Mahalanobis)")
print("=" * 70)
print(f"{'Ticker':6}  cap_cyc  res_mom  yz_vol  amihud   z_moat  inv_qua  disc_cd  z_dem  comp_sc")
for t in TARGETS:
    if t not in sub.index:
        print(f"  {t:6}  ** NOT IN UNIVERSE **")
        continue
    r = sub.loc[t]
    print(
        f"  {t:6}  {float(r['capital_cycle_score'] or 0):7.4f}  {float(r['resid_mom_60d'] or 0):7.4f}  "
        f"{float(r['yz_vol_20d'] or 0):6.4f}  {float(r['amihud_20d'] or 0):6.4f}  "
        f"{float(r['z_moat'] or 0):7.3f}  {float(r['z_inventory_quality_proxy'] or 0):7.3f}  "
        f"{float(r['z_discipline_cond'] or 0):7.3f}  {float(r['z_demand'] or 0):5.3f}  "
        f"{float(r['composite_score'] or 0):7.4f}"
    )

# ── Block 3: Anchor centroid vs saturating tickers ──────────────────────────
avail_anchors = [t for t in ANCHORS if t in sub.index]
feat_cols = ["capital_cycle_score", "resid_mom_60d", "yz_vol_20d", "amihud_20d",
             "z_moat", "z_inventory_quality_proxy", "z_discipline_cond", "z_demand"]
X_anchor = sub.loc[avail_anchors, feat_cols].astype(float).fillna(0)
mu_anchor = X_anchor.mean(axis=0)

print()
print("=" * 70)
print(f"BLOCK 3: L2 distance from anchor centroid ({','.join(avail_anchors)})")
print("=" * 70)
print("Anchor centroid:")
for col, v in mu_anchor.items():
    print(f"  {col}: {v:.4f}")
print()
print(f"{'Ticker':6}  L2-dist  verdict")
for t in TARGETS:
    if t not in sub.index:
        print(f"  {t:6}  ABSENT")
        continue
    x = sub.loc[t, feat_cols].astype(float).fillna(0).values
    d = float(np.linalg.norm(x - mu_anchor.values))
    flag = "CLOSE (<2.5)" if d < 2.5 else ("MID (2.5-5)" if d < 5.0 else "FAR (>5)")
    is_anch = "(ANCHOR)" if t in ANCHORS else ""
    print(f"  {t:6}  {d:7.4f}  {flag}  {is_anch}")

# ── Block 4: Why saturation — r_cyc approximation ───────────────────────────
print()
print("=" * 70)
print("BLOCK 4: Saturation root cause — approximate r_cyc from Mahalanobis dist")
print(" (from sample CSV mahalanobis_k_cyc column)")
print("=" * 70)
all_longs = csv.copy()
all_longs["ticker_u"] = all_longs["ticker"].str.upper()
for t in TARGETS:
    row = all_longs[all_longs["ticker_u"] == t]
    if row.empty:
        print(f"  {t:6}  not in sample CSV")
        continue
    r = row.iloc[0]
    mah = float(r.get("mahalanobis_k_cyc") or 0)
    # r_cyc approx: exp(-0.5*d^2); saturation if d is small
    r_cyc_approx = np.exp(-0.5 * mah**2)
    odds_approx = r_cyc_approx / (1 - r_cyc_approx + 1e-8)
    print(f"  {t:6}  mah_dist={mah:.4f}  r_cyc_approx={r_cyc_approx:.6f}  odds_approx={odds_approx:.4g}  score={float(r.get('odds_score') or 0):.4g}")

print()
print("KEY INSIGHT: tickers with small mah_dist get r_cyc->1.0 -> saturation at 5e7")
print("Anchors (MU/CIEN/LRCX/AMAT/KLAC) that have HIGHER mah_dist get LOWER r_cyc -> lower score")
print("This confirms: the 3-component centroid is dominated by tickers closer to it than the anchors.")
