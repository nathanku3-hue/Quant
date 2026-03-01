import wrds
import sys

db = wrds.Connection(wrds_username="nathanku3")

print('--- ob_w_company_id_table_lms INFO ---')
desc = db.describe_table('bvd_orbis_trial', 'ob_w_company_id_table_lms')
for _, r in desc.iterrows():
    if any(k in r['name'].lower() for k in ['bvd', 'naics', 'status', 'id', 'nace', 'ind', 'isoc', 'stat']):
        print(f"{r['name']}: {r['type']}")

print('\n--- ob_w_ind_g_fins_cfl_usd_lms INFO ---')
desc2 = db.describe_table('bvd_orbis_trial', 'ob_w_ind_g_fins_cfl_usd_lms')
for _, r in desc2.iterrows():
    name = r['name'].lower()
    if 'bvd' in name or 'rev' in name or 'asse' in name or 'inv' in name or 'stock' in name or 'date' in name or 'stk' in name or 'ass' in name:
        print(f"{r['name']}: {r['type']}")
