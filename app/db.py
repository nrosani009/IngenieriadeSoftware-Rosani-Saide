"""Persistencia SQLite para el prototipo."""
from contextlib import contextmanager
import sqlite3
from pathlib import Path
import os

DB_PATH = os.getenv("TROTAMUNDOS_DB", str(Path(__file__).resolve().parent.parent / "trotamundos.db"))
ANALYTICS_DB_PATH = os.getenv("TROTAMUNDOS_ANALYTICS_DB", str(Path(__file__).resolve().parent.parent / "analytics.db"))

@contextmanager
def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
            owner TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('flight','hotel','car','train','bus','other')),
            provider TEXT NOT NULL,
            confirmation_code TEXT,
            start_at TEXT,
            end_at TEXT,
            destination TEXT,
            status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled')),
            source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','email','provider')),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            sender TEXT NOT NULL,
            UNIQUE(owner, sender)
        );
        CREATE TABLE IF NOT EXISTS processed_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            message_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            result TEXT NOT NULL,
            reservation_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(owner, message_id)
        );
        CREATE TABLE IF NOT EXISTS support_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            message TEXT NOT NULL,
            classification TEXT NOT NULL,
            status TEXT NOT NULL,
            agency TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
    with connect(ANALYTICS_DB_PATH) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS reservation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            reservation_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            kind TEXT NOT NULL,
            destination TEXT,
            event_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

def rowdict(row):
    return dict(row) if row else None
