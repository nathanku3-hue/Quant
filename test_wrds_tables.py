import wrds

db = wrds.Connection(wrds_username="nathanku3")

print("\n--- ACTION 1: MAP ORBIS TRIAL TABLES ---")
orbis_tables = db.list_tables('bvd_orbis_trial')
print(orbis_tables)

print("\n--- ACTION 2: INSPECT KEY FINANCIAL AND INDUSTRY TABLES ---")
target_tables = []
for t in orbis_tables:
    tl = t.lower()
    if any(k in tl for k in ['ind', 'sector', 'meta', 'comp', 'naics', 'fin', 'bal', 'inc']):
        target_tables.append(t)

print("Target tables found:", target_tables)

for t in target_tables[:5]:  # Limit just in case there are too many initially
    print(f"\nSchema for: {t}")
    try:
        schema = db.describe_table('bvd_orbis_trial', t)
        print(schema)
    except Exception as e:
        print("Error describing table:", e)

print("\n--- ACTION 3: HUNT FOR M&A DATA ---")
bvd_tables = db.list_tables('bvd')
osiris_tables = db.list_tables('bvd_osiris')

ma_tables = []
for t in bvd_tables + osiris_tables:
    tl = t.lower()
    if any(k in tl for k in ['merg', 'acq', 'deal', 'm_a', 'ma']):
        ma_tables.append(t)

print("M&A tables found across bvd / bvd_osiris:")
print(ma_tables)

