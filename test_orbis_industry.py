import wrds
import pandas as pd

if __name__ == "__main__":
    db = wrds.Connection(wrds_username='nathanku3')

    print('--- CHECKING orbis_qvards ---')
    try:
        desc = db.describe_table('bvd_orbis_trial', 'orbis_qvards')
        for _, r in desc.iterrows():
            if 'naic' in r['name'].lower() or 'sic' in r['name'].lower() or 'ind' in r['name'].lower():
                print(r['name'], r['type'])
        if len(desc) < 20:
             print(desc[['name', 'type']].to_string())
    except Exception as e:
        print('Error:', e)

    print('\n--- HUNTING FOR NAICS/SIC IN bvd_orbis_trial SCHEMAS ---')
    tables = db.list_tables('bvd_orbis_trial')
    found_cols = []
    for t in tables:
        try:
            desc = db.describe_table('bvd_orbis_trial', t)
            for _, r in desc.iterrows():
                name = r['name'].lower()
                if 'naics' in name or 'sic' in name or 'ind' in name or 'nace' in name:
                    found_cols.append(f"{t}.{r['name']} ({r['type']})")
        except: pass
    
    for f in found_cols: print('Found:', f)
