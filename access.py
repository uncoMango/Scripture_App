import sqlite3
import uuid
import os

DB_PATH = os.environ.get("ACCESS_DB_PATH", "/var/data/access_codes.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_codes (
                code       TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def generate_code(email: str) -> str:
    raw  = uuid.uuid4().hex[:12].upper()
    code = f"KAHU-{raw[0:4]}-{raw[4:8]}-{raw[8:12]}"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO access_codes (code, email) VALUES (?, ?)", (code, email))
    return code


def validate_code(code: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT code FROM access_codes WHERE code = ?", (code,)
        ).fetchone()
    return row is not None
