import wrds

print("Initializing WRDS connection...")
# wrds.Connection() uses pgpass if available
db = wrds.Connection()
print("Listing libraries...")
libraries = db.list_libraries()

print("All libraries count:", len(libraries))
matches = [
    lib for lib in libraries 
    if any(term in lib.lower() for term in ['bvd', 'orbis', 'osiris', 'bankfocus'])
]
print("BvD matches found:", matches)
