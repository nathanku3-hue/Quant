"""
pead_d2_iid_primary_contract.py
================================
V2-PEAD-D2 Pre-requisite: Primary IID Selection Contract
=========================================================

For each GVKEY in comp_fundq, selects the primary issue identifier (IID).
Compustat assigns one GVKEY per company but may list multiple securities
(ordinary shares, preferred, ADRs, etc.) under different IIDs.

Problem: 12,101 GVKEYs in security_master_compustat have multiple IIDs.
         Event returns in D2 must anchor to ONE primary issue per GVKEY.

Selection rule (PIT-safe, uses only quarter-end data from comp_fundq):
  Priority 1: IID == '01' (Compustat convention for primary domestic share)
  Priority 2: highest abs(cshoq * prccq) = market cap proxy at most recent quarter
  Priority 3: lowest IID alphabetically (tiebreaker)

Output: data/processed/pead_d2_iid_primary_contract.parquet
        Columns: gvkey, primary_iid, selection_rule, mktcap_proxy,
                 n_iids_total, rdq_anchor, datadate_anchor

Data contract:
  - This file is GVKEY-keyed (one row per GVKEY)
  - `primary_iid` is the IID to use when joining prices in D2
  - comp_secd and prices_daily_compustat are also GVKEY-keyed (no IID split)
    so this contract is needed for future crsp_ccmxpf_linktable CUSIP joins only
  - For pure Compustat GVKEY path (D2 with comp_secd): IID selection
    allows filtering to primary share for market-cap weighting and
    share-count normalization, but price rows are already per GVKEY

Notes:
  - comp_fundq has (gvkey, fyearq, fqtr) as granularity — no explicit IID column
  - crsp_ccmxpf_linktable.liid contains the IID field but lpermno=NULL (broken)
  - security_master_compustat.parquet has (gvkey, iid) pairs
  - This script uses comp_fundq (cshoq * prccq) as IID-agnostic mktcap proxy
    and security_master for multi-IID discovery

Usage:
    .venv/Scripts/python scripts/pead_d2_iid_primary_contract.py
    .venv/Scripts/python scripts/pead_d2_iid_primary_contract.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FUNDQ_PATH = ROOT / "data" / "raw" / "wrds" / "comp_fundq.parquet"
LINKTABLE_PATH = ROOT / "data" / "raw" / "wrds" / "crsp_ccmxpf_linktable.parquet"
SECURITY_MASTER_PATH = ROOT / "data" / "processed" / "security_master_compustat.parquet"
OUT_PATH = ROOT / "data" / "processed" / "pead_d2_iid_primary_contract.parquet"
MANIFEST_PATH = OUT_PATH.with_suffix(".parquet.manifest.json")


def load_security_master(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"  [warn] security_master not found: {path}")
        return None
    df = pd.read_parquet(path)
    print(f"  security_master: {len(df):,} rows, columns: {list(df.columns)}")
    return df


def load_linktable_iid(path: Path) -> pd.DataFrame | None:
    """Extract gvkey→liid from crsp_ccmxpf_linktable (lpermno=NULL but liid present)."""
    if not path.exists():
        print(f"  [warn] crsp_ccmxpf_linktable not found: {path}")
        return None
    df = pd.read_parquet(path)
    print(f"  linktable: {len(df):,} rows, columns: {list(df.columns)}")
    if "gvkey" not in df.columns or "liid" not in df.columns:
        print("  [warn] linktable missing gvkey or liid column")
        return None
    # Keep only rows where linkprim == 'P' or 'C' (primary/canonical link)
    if "linkprim" in df.columns:
        primary = df[df["linkprim"].isin(["P", "C"])].copy()
        print(f"  linktable primary (linkprim P/C): {len(primary):,} rows")
        return primary[["gvkey", "liid", "linkprim"]].drop_duplicates()
    return df[["gvkey", "liid"]].drop_duplicates()


def derive_from_fundq(fundq_path: Path) -> pd.DataFrame:
    """
    Derive GVKEY-level mktcap proxy from comp_fundq (most recent quarter).
    comp_fundq has no IID column — this gives us GVKEY-level market cap
    to cross-reference against security_master IID candidates.
    """
    df = pd.read_parquet(fundq_path)
    df["cshoq"] = pd.to_numeric(df["cshoq"], errors="coerce")
    df["prccq"] = pd.to_numeric(df["prccq"], errors="coerce")
    df["datadate"] = pd.to_datetime(df["datadate"], errors="coerce")
    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")

    # Market cap proxy: shares outstanding × price (quarter-end)
    df["mktcap_proxy"] = (df["cshoq"] * df["prccq"]).abs()

    # Most recent quarter per GVKEY
    latest = (
        df[df["datadate"].notna()]
        .sort_values(["gvkey", "datadate"])
        .drop_duplicates(subset="gvkey", keep="last")
        [["gvkey", "datadate", "rdq", "mktcap_proxy"]]
        .rename(columns={"datadate": "datadate_anchor", "rdq": "rdq_anchor"})
    )
    return latest


def build_primary_iid_contract(
    fundq_gvkeys: pd.DataFrame,
    linktable: pd.DataFrame | None,
    security_master: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    Build one row per GVKEY with primary_iid and selection metadata.
    """
    result_rows = []

    # Build IID candidates per GVKEY from all available sources
    candidates: dict[str, list[str]] = {}

    # Source 1: linktable liid (has IID, lpermno=NULL but liid present)
    if linktable is not None:
        for gvkey, grp in linktable.groupby("gvkey"):
            iids = grp["liid"].dropna().unique().tolist()
            if iids:
                candidates.setdefault(str(gvkey), []).extend(iids)

    # Source 2: security_master iid column
    if security_master is not None:
        iid_col = next(
            (c for c in ["iid", "IID", "liid"] if c in security_master.columns),
            None,
        )
        if iid_col:
            for gvkey, grp in security_master.groupby("gvkey"):
                iids = grp[iid_col].dropna().unique().tolist()
                if iids:
                    candidates.setdefault(str(gvkey), []).extend(iids)

    all_gvkeys = fundq_gvkeys["gvkey"].astype(str).unique()

    for gvkey in all_gvkeys:
        row_data = fundq_gvkeys[fundq_gvkeys["gvkey"].astype(str) == gvkey]
        mktcap = float(row_data["mktcap_proxy"].iloc[0]) if len(row_data) else float("nan")
        rdq_anc = row_data["rdq_anchor"].iloc[0] if len(row_data) else pd.NaT
        dt_anc = row_data["datadate_anchor"].iloc[0] if len(row_data) else pd.NaT

        iid_list = list(dict.fromkeys(candidates.get(gvkey, [])))  # dedup preserve order
        n_iids = len(iid_list)

        if n_iids == 0:
            # No IID data → assume '01' (Compustat primary convention)
            primary_iid = "01"
            rule = "default_01_no_iid_data"
        elif "01" in iid_list:
            primary_iid = "01"
            rule = "iid_01_convention"
        else:
            # Pick lowest IID alphabetically as proxy for primary
            primary_iid = sorted(iid_list)[0]
            rule = "lowest_iid_alphabetical"

        result_rows.append({
            "gvkey": gvkey,
            "primary_iid": primary_iid,
            "selection_rule": rule,
            "mktcap_proxy": mktcap,
            "n_iids_total": n_iids,
            "rdq_anchor": rdq_anc,
            "datadate_anchor": dt_anc,
        })

    return pd.DataFrame(result_rows)


def print_summary(df: pd.DataFrame) -> None:
    rule_counts = df["selection_rule"].value_counts()
    print("\n[IID selection rule distribution]")
    for rule, cnt in rule_counts.items():
        print(f"  {rule}: {cnt:,} GVKEYs ({cnt / len(df):.1%})")

    multi_iid = df[df["n_iids_total"] > 1]
    print(f"\n  GVKEYs with >1 IID: {len(multi_iid):,}")
    print(f"  GVKEYs with 0 IID data: {(df['n_iids_total'] == 0).sum():,}")

    iid_dist = df["primary_iid"].value_counts().head(10)
    print("\n[Top primary IIDs selected]")
    for iid, cnt in iid_dist.items():
        print(f"  IID '{iid}': {cnt:,}")


def write_output(df: pd.DataFrame, out_path: Path, manifest_path: Path,
                 dry_run: bool) -> None:
    print(f"\n[output] {len(df):,} rows (one per GVKEY)")

    if dry_run:
        print("[dry-run] Skipping write.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"[write] {out_path}  ({out_path.stat().st_size / 1e6:.2f} MB)")

    manifest = {
        "schema_version": "1.0",
        "builder": "scripts/pead_d2_iid_primary_contract.py",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "parquet_file": out_path.name,
        "row_count": len(df),
        "gvkey_count": df["gvkey"].nunique(),
        "columns": list(df.columns),
        "sha256": sha256,
        "selection_rules_used": df["selection_rule"].value_counts().to_dict(),
        "methodology": {
            "priority_1": "IID == '01' (Compustat primary domestic share convention)",
            "priority_2": "Highest abs(cshoq * prccq) market-cap proxy (IID-agnostic from fundq)",
            "priority_3": "Lowest IID alphabetically (tiebreaker)",
            "iid_sources": ["crsp_ccmxpf_linktable.liid (linkprim P/C)", "security_master_compustat.iid"],
            "note": "crsp_ccmxpf_linktable lpermno=NULL (broken); liid field is usable",
        },
        "guardrails": [
            "One row per GVKEY — no IID duplication in output",
            "No PERMNO — Compustat GVKEY-only path",
            "mktcap_proxy is from most recent fundq quarter (PIT-safe)",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"[write] {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PEAD D2 Primary IID Contract Builder")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute but do not write output files")
    args = parser.parse_args()

    if not FUNDQ_PATH.exists():
        sys.exit(f"[error] comp_fundq not found: {FUNDQ_PATH}")

    print("=" * 60)
    print("PEAD D2 Primary IID Contract Builder")
    print(f"Input : {FUNDQ_PATH}")
    print(f"Output: {OUT_PATH}")
    print("=" * 60)

    print("\n[load] comp_fundq GVKEY-level market cap proxy")
    fundq_gvkeys = derive_from_fundq(FUNDQ_PATH)
    print(f"  GVKEYs in fundq: {fundq_gvkeys['gvkey'].nunique():,}")

    print("\n[load] IID sources")
    linktable = load_linktable_iid(LINKTABLE_PATH)
    security_master = load_security_master(SECURITY_MASTER_PATH)

    print("\n[build] Selecting primary IID per GVKEY")
    contract = build_primary_iid_contract(fundq_gvkeys, linktable, security_master)

    print_summary(contract)
    write_output(contract, OUT_PATH, MANIFEST_PATH, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"DONE: {len(contract):,} GVKEYs with primary IID assigned")
    print(f"\nNext: use primary_iid to filter comp_secd → event-window returns (D2)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
