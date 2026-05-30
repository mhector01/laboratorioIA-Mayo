import sqlite3

# Check eventos_acceso.db
con = sqlite3.connect('eventos_acceso.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('eventos_acceso.db tables:', cur.fetchall())
cur.execute("PRAGMA table_info(eventos_acceso);")
print('Columns:', cur.fetchall())
cur.execute("SELECT * FROM eventos_acceso LIMIT 10;")
print('Data:', cur.fetchall())
con.close()

print()

# Check vision_guard.db
con2 = sqlite3.connect('vision_guard.db')
cur2 = con2.cursor()
cur2.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('vision_guard.db tables:', cur2.fetchall())
cur2.execute("SELECT * FROM sqlite_master WHERE type='table';")
tables = cur2.fetchall()
for t in tables:
    cur2.execute(f"PRAGMA table_info({t[0]});")
    print(f'Columns of {t[0]}:', cur2.fetchall())
    cur2.execute(f"SELECT * FROM {t[0]} LIMIT 10;")
    print(f'Data of {t[0]}:', cur2.fetchall())
con2.close()
