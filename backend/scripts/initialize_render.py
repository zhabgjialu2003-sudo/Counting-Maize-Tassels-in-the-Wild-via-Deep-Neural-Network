"""Initialise an empty Render database without resetting existing data."""

from __future__ import annotations

from pathlib import Path

import psycopg

from backend.database import db_config
from backend.migrations import apply_migrations
from backend.scripts.configure_demo_accounts import main as configure_demo_accounts


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA = PROJECT_ROOT / "database" / "schema" / "schema_postgresql.sql"


def application_schema_state(connection) -> tuple[bool, bool]:
    row = connection.execute(
        """
        SELECT
            to_regclass('public.users') IS NOT NULL AS users_present,
            EXISTS (
                SELECT 1
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename IN (
                      'roles', 'users', 'images', 'image_files',
                      'detection_results', 'datasets', 'fields'
                  )
            ) AS application_tables_present
        """
    ).fetchone()
    if isinstance(row, dict):
        return bool(row["users_present"]), bool(row["application_tables_present"])
    return bool(row[0]), bool(row[1])


def ensure_base_schema(connection, schema_path: Path = BASE_SCHEMA) -> bool:
    """Apply the base schema once; return True only when it was applied."""
    users_present, application_tables_present = application_schema_state(connection)
    if users_present:
        return False
    if application_tables_present:
        raise RuntimeError(
            "A partial application schema exists without the users table; "
            "automatic initialisation was stopped to protect existing data"
        )
    schema_sql = schema_path.read_text(encoding="utf-8")
    connection.execute(schema_sql)
    return True


def main() -> int:
    with psycopg.connect(**db_config()) as connection:
        created = ensure_base_schema(connection)
    print("created: base schema" if created else "verified: existing base schema")

    apply_migrations()
    pending = [
        item["name"]
        for item in apply_migrations(check_only=True)
        if item["state"] != "applied"
    ]
    if pending:
        raise RuntimeError("Database migrations are not ready: " + ", ".join(pending))

    configure_demo_accounts()
    print("verified: database migrations and assessment accounts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
