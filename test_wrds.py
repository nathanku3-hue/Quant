import wrds

try:
    print("Testing WRDS...")
    db = wrds.Connection(wrds_username="nathanku3")
    libraries = db.list_libraries()
    bvd_libs = [l for l in libraries if any(t in l.lower() for t in ["bvd", "orbis", "osiris", "bankfocus"])]
    print("\n--- RESULTS ---")
    print("Libraries found:", len(libraries))
    print("BvD matches:", bvd_libs)
except Exception as e:
    print("Connection error:", str(e))
