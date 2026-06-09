"""PostgreSQL connection helper for Maize Detector API."""

import psycopg2
import psycopg2.extras
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "maize_detector"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
    "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "3")),
    "options": f"-c statement_timeout={int(os.getenv('PGSTATEMENT_TIMEOUT_MS', '5000'))}",
}


def get_db():
    """Return a new database connection with RealDictCursor."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def query(sql, params=None, fetchone=False):
    """Execute a query and return results. Short-lived connection per call."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if sql.strip().upper().startswith(("SELECT", "WITH", "RETURNING")):
            if fetchone:
                row = cur.fetchone()
                return dict(row) if row else None
            return [dict(r) for r in (cur.fetchall() or [])]
        conn.commit()
        return {"affected": cur.rowcount}
    finally:
        conn.close()


def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE and return affected row count."""
    return query(sql, params)
