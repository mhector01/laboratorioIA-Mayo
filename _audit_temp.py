import sqlite3

con = sqlite3.connect('smart_gate.db')
cur = con.cursor()

# Get table list
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('Tables:', tables)

for t in tables:
    print(f'\n--- Table: {t[0]} ---')
    cur.execute(f"PRAGMA table_info({t[0]});")
    cols = cur.fetchall()
    for c in cols:
        print(c)
    cur.execute(f"SELECT * FROM {t[0]} LIMIT 10;")
    rows = cur.fetchall()
    for r in rows:
        print(r)

con.close()
