import wrds
print("Connecting...")
db = wrds.Connection(wrds_username="nathanku3")
libraries = db.list_libraries()
matches = [l for l in libraries if any(t in l.lower() for t in ['bvd', 'orbis', 'osiris', 'bankfocus'])]
print("MATHCES:", matches)
