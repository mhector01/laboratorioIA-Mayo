import sqlite3
import time

DB_PATH = "eventos_acceso.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_acceso (
            id_evento     INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     REAL    NOT NULL,
            usuario       TEXT,
            ubicacion     TEXT,
            confianza     REAL,
            tipo_evento   TEXT    NOT NULL DEFAULT 'acceso',
            accion_tomada TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp
        ON eventos_acceso(timestamp)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_usuario
        ON eventos_acceso(usuario)
    """)

    conn.commit()
    conn.close()
