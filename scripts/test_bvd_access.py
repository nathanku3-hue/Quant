import wrds
import pandas as pd
import sys


def probe_library(db, lib_name, search_terms):
    """
    Probes a WRDS library for access.
    1. Lists tables.
    2. Ranks tables based on search_terms.
    3. Attempts a SELECT * LIMIT 5 on the best candidate.
    """
    print(f"--- Probing {lib_name} ---")
    try:
        tables = db.list_tables(lib_name)
        if not tables:
            return "LOCKED (or empty)", 0, None
    except Exception as e:
        return f"LOCKED (List Error: {str(e)})", 0, None

    # Find best candidate table (prioritize tables with 'ind', 'fin', 'company')
    candidates = []
    for t in tables:
        score = 0
        for term in search_terms:
            if term in t.lower():
                score += 1
        if score > 0:
            candidates.append((score, t))

    # Sort by score desc, then length asc (shorter names often main tables)
    candidates.sort(key=lambda x: (-x[0], len(x[1])))

    # If no candidates match terms, try the first table as a hail mary
    target_tables = [c[1] for c in candidates] if candidates else tables[:3]

    for table in target_tables:
        print(f"  > Attempting access: {lib_name}.{table}...")
        try:
            # Try to fetch 5 rows
            sample_query = f"SELECT * FROM {lib_name}.{table} LIMIT 5"
            df = db.raw_sql(sample_query)

            # Try metadata row-count (fast); fallback to sample row count
            try:
                row_count = db.get_row_count(lib_name, table)
            except Exception:
                row_count = len(df)

            return "OPEN", row_count, table

        except Exception as e:
            error_str = str(e).lower()
            if "permission denied" in error_str or "insufficientprivilege" in error_str:
                print(f"    x Permission Denied on {table}")
                # Don't return yet, try next candidate
                continue
            else:
                print(f"    x Error on {table}: {str(e)}")
                continue

    return "LOCKED (All candidates failed)", 0, None


def main():
    try:
        print("Connecting to WRDS...")
        db = wrds.Connection()
        print("Connected.")
    except Exception as e:
        print(f"CRITICAL: Could not connect to WRDS. {e}")
        return

    # 1. Probe Osiris (Public Global)
    # Target: 'industrials', 'companies', 'financials'
    osiris_status, osiris_count, osiris_table = probe_library(
        db, "bvd_osiris", ["industrial", "company", "master", "ratio"]
    )

    # 2. Probe Amadeus (European Private)
    # Target: 'fins', 'company', 'index'
    amadeus_status, amadeus_count, amadeus_table = probe_library(
        db, "bvd_amadeus_trial", ["fin", "company", "large", "medium"]
    )

    print("\n" + "=" * 40)
    print("       PHASE 25 ACCESS REPORT")
    print("=" * 40)
    print(f"Osiris Status:  {osiris_status}")
    if osiris_status == "OPEN":
        print(f"   - Table: {osiris_table}")
        print(f"   - Rows:  {osiris_count}")

    print("-" * 40)
    print(f"Amadeus Status: {amadeus_status}")
    if amadeus_status == "OPEN":
        print(f"   - Table: {amadeus_table}")
        print(f"   - Rows:  {amadeus_count}")
    print("=" * 40)


if __name__ == "__main__":
    main()
