"""
storage.py
----------
SQLite-backed persistence for incidents. Replaces the earlier flat
JSON file (which was rewritten in full on every save — fine for a
handful of records, but risky for concurrent writes and doesn't scale).
Each incident is stored as one row with its full JSON payload in a
TEXT column, which keeps the schema simple while still giving us
transactional writes and indexed lookups.

Public functions (`load_incidents`, `save_incident`, plus new
`clear_incidents`, `count_incidents`) match/extend the original
storage.py API so app.py needs minimal changes.
"""
import json
import os
import sqlite3
from contextlib import contextmanager

from config import DATABASE_PATH


def _ensure_parent_dir():
    parent = os.path.dirname(DATABASE_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)


@contextmanager
def _connect():
    _ensure_parent_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT UNIQUE NOT NULL,
                scenario TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        conn.commit()


def save_incident(incident):
    """Persist one incident. Raises sqlite3.Error on failure — callers
    should catch and translate to an HTTP error response."""
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO incidents (incident_id, scenario, timestamp, payload) "
            "VALUES (?, ?, ?, ?)",
            (
                incident["incident_id"],
                incident["scenario"],
                incident["timestamp"],
                json.dumps(incident),
            ),
        )
        conn.commit()


def load_incidents():
    """Return all incidents, oldest first, matching the original JSON
    file's ordering behavior."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT payload FROM incidents ORDER BY id ASC"
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def clear_incidents():
    """Delete all stored incidents. Used by DELETE /api/incidents."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM incidents")
        conn.commit()


def count_incidents():
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()
    return row[0] if row else 0
