"""Shared PostgreSQL connection configuration for the API and utilities."""

from __future__ import annotations

import os
from contextlib import contextmanager

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None


def db_config() -> dict[str, str | int]:
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "maize_detector"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
        "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "3")),
        "options": f"-c statement_timeout={int(os.getenv('PGSTATEMENT_TIMEOUT_MS', '5000'))}",
    }


@contextmanager
def db_connection():
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    config = db_config()
    if not config["password"]:
        raise RuntimeError("PGPASSWORD is not configured")
    conn = psycopg.connect(**config, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
