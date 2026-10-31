import sqlite3, sys

for path in ["backend/payshield.db", "backend/app/data/fallback/payshield_snapshot.db"]:
    print("\n" + "#" * 60)
    print("DB:", path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for t in tables:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} rows")
