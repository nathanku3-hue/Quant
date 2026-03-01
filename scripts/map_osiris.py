from __future__ import annotations

from dataclasses import dataclass

import wrds


FINANCIAL_KEYWORDS = ("inv", "stk", "rev", "sale", "turnover")
INDUSTRY_KEYWORDS = ("naics", "sic", "ind", "sector")
LOCATION_KEYWORDS = ("iso", "country", "nation")


@dataclass
class TableMatch:
    table: str
    financial_hits: list[str]
    industry_hits: list[str]
    location_hits: list[str]


def _keyword_hits(columns_lower: list[str], keywords: tuple[str, ...]) -> list[str]:
    return [kw for kw in keywords if any(kw in col for col in columns_lower)]


def main() -> None:
    library = "bvd_osiris"
    print(f"Connecting to WRDS for library: {library}")
    db = wrds.Connection()

    print("\nListing all tables...")
    tables = sorted(db.list_tables(library))
    print(f"Total tables in {library}: {len(tables)}")
    for name in tables:
        print(f" - {name}")

    print("\nScanning table schemas for keyword matches...")
    candidates: list[TableMatch] = []
    describe_failures: list[tuple[str, str]] = []
    table_columns: dict[str, list[str]] = {}

    for table in tables:
        try:
            desc = db.describe_table(library, table)
        except Exception as exc:
            describe_failures.append((table, str(exc)))
            continue

        if desc is None or desc.empty:
            continue

        column_names = [str(col) for col in desc["name"].tolist()]
        table_columns[table] = column_names
        columns_lower = [col.lower() for col in column_names]
        financial_hits = _keyword_hits(columns_lower, FINANCIAL_KEYWORDS)
        industry_hits = _keyword_hits(columns_lower, INDUSTRY_KEYWORDS)
        location_hits = _keyword_hits(columns_lower, LOCATION_KEYWORDS)

        if financial_hits and industry_hits:
            candidates.append(
                TableMatch(
                    table=table,
                    financial_hits=financial_hits,
                    industry_hits=industry_hits,
                    location_hits=location_hits,
                )
            )

    print("\nColumns by table:")
    for table in tables:
        cols = table_columns.get(table)
        if not cols:
            print(f" - {table}: <no columns returned>")
            continue
        print(f" - {table}:")
        for col in cols:
            print(f"    - {col}")

    print("\nCandidate tables with BOTH Financial and Industry-code signals:")
    if not candidates:
        print(" - None found.")
    else:
        for match in candidates:
            print(
                f" - {match.table} | financial={match.financial_hits} "
                f"| industry={match.industry_hits} | location={match.location_hits or ['none']}"
            )

    print("\nColumns in bvd_osiris.os_stock_ratios:")
    try:
        ratios = db.describe_table(library, "os_stock_ratios")
        if ratios is None or ratios.empty:
            print(" - No columns returned.")
        else:
            for col in ratios["name"].tolist():
                print(f" - {col}")

            ratio_cols_lower = [str(col).lower() for col in ratios["name"].tolist()]
            turnover_like = [c for c in ratio_cols_lower if "turnover" in c or "invent" in c]
            print("\nTurnover/inventory-like columns in os_stock_ratios:")
            if turnover_like:
                for col in turnover_like:
                    print(f" - {col}")
            else:
                print(" - None found.")
    except Exception as exc:
        print(f" - Failed to describe os_stock_ratios: {exc}")

    if describe_failures:
        print("\nSchema describe failures:")
        for table, err in describe_failures:
            print(f" - {table}: {err}")

    db.close()


if __name__ == "__main__":
    main()
