import sqlite3
from datetime import datetime, timezone
DB_FILE = "urls.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            url TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_urls(domain, urls):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    datos = [(domain, u["url"], u["timestamp"]) for u in urls]
    c.executemany(
        "INSERT INTO urls (domain, url, timestamp) VALUES (?, ?, ?)",
        datos
    )
    conn.commit()
    conn.close()