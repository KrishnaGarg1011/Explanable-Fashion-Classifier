# backend/database.py
import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            uploaded_at TEXT,
            label TEXT,
            confidence REAL,
            explanation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_image(filename, label, confidence, explanation):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO images (filename, uploaded_at, label, confidence, explanation)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, datetime.utcnow().isoformat(), label, confidence, explanation))
    conn.commit()
    conn.close()

def get_all_images():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM images ORDER BY uploaded_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

init_db()
