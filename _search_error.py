import sqlite3

# Check all databases for 'Error_IA'
for db in ['smart_gate.db', 'eventos_acceso.db', 'vision_guard.db']:
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        print(f'\n=== {db} ===')
        for table in tables:
            cur.execute(f"PRAGMA table_info({table});")
            cols = cur.fetchall()
            # Check each column for Error_IA
            for col in cols:
                col_name = col[1]
                if col_name in ('estado', 'tipo_evento', 'accion_tomada', 'tipo'):
                    cur.execute(f"SELECT DISTINCT {col_name} FROM {table} WHERE {col_name} LIKE '%Error%' OR {col_name} LIKE '%IA%';")
                    results = cur.fetchall()
                    if results:
                        print(f'  Table {table}, column {col_name}: {results}')
            # Also search anywhere for exact match
            for col in cols:
                col_name = col[1]
                if col_name not in ('id', 'id_evento', 'timestamp', 'fecha', 'confianza', 'score_confianza', 'snapshots', 'nombre', 'seq', 'name'):
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} = 'Error_IA';")
                        count = cur.fetchone()[0]
                        if count > 0:
                            print(f'  Found {count} rows in {table}.{col_name} = Error_IA')
                    except:
                        pass
        con.close()
    except Exception as e:
        print(f'Error with {db}: {e}')
