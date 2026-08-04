"""Small PostgreSQL migration runner for local and deployed environments."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

try:
    from .database import db_config
except ImportError:
    from database import db_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"
LOCK_ID = 260207


@dataclass(frozen=True)
class Migration:
    name: str
    path: Path
    sql: str
    sha256: str


def _transaction_body(sql: str) -> str:
    lines = sql.splitlines()
    return "\n".join(
        line for line in lines if line.strip().upper() not in {"BEGIN;", "COMMIT;"}
    ).strip()


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    migrations = []
    for path in sorted(directory.glob("[0-9][0-9][0-9]_*.sql")):
        raw = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                name=path.name,
                path=path,
                sql=_transaction_body(raw),
                sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            )
        )
    return migrations


def connection_kwargs() -> dict[str, str | int]:
    return db_config()


def migration_status(conn, migrations: list[Migration]) -> list[dict[str, str]]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_name VARCHAR(255) PRIMARY KEY,
            checksum_sha256 CHAR(64) NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    rows = conn.execute(
        "SELECT migration_name, checksum_sha256 FROM schema_migrations"
    ).fetchall()
    applied = {row["migration_name"]: row["checksum_sha256"] for row in rows}
    status = []
    for migration in migrations:
        recorded = applied.get(migration.name)
        state = "pending" if recorded is None else (
            "applied" if recorded == migration.sha256 else "checksum-mismatch"
        )
        status.append({"name": migration.name, "state": state})
    return status


def apply_migrations(*, check_only: bool = False) -> list[dict[str, str]]:
    migrations = discover_migrations()
    with psycopg.connect(**connection_kwargs(), row_factory=dict_row) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
        status = migration_status(conn, migrations)
        mismatches = [item["name"] for item in status if item["state"] == "checksum-mismatch"]
        if mismatches:
            raise RuntimeError(
                "Applied migration files changed: " + ", ".join(mismatches)
            )
        if check_only:
            conn.rollback()
            return status
        for migration, item in zip(migrations, status, strict=True):
            if item["state"] != "pending":
                continue
            conn.execute(migration.sql)
            conn.execute(
                "INSERT INTO schema_migrations (migration_name, checksum_sha256) VALUES (%s, %s)",
                (migration.name, migration.sha256),
            )
            item["state"] = "applied"
        return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply maize project database migrations")
    parser.add_argument("--check", action="store_true", help="Report status without applying changes")
    args = parser.parse_args()
    for item in apply_migrations(check_only=args.check):
        print(f"{item['state']}: {item['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
