import builtins
import getpass
builtins.input = lambda prompt: "nathanku3"
getpass.getpass = lambda prompt: "7859628Nathan"

import wrds

try:
    print("Testing WRDS bypass...")
    db = wrds.Connection(wrds_username="nathanku3")
    libraries = db.list_libraries()
    bvd_libs = [l for l in libraries if any(t in l.lower() for t in ["bvd", "orbis", "osiris", "bankfocus"])]
    print("\n--- RESULTS ---")
    print("Libraries found:", len(libraries))
    print("BvD matches:", bvd_libs)
except Exception as e:
    print("Connection error:", type(e).__name__, str(e))
