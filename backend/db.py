"""PostgreSQL connection helper for Maize Detector API."""

import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "maize_detector"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "123456"),
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
