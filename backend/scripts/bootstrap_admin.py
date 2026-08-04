"""Create or rotate the initial administrator without a stored default password."""

from __future__ import annotations

import getpass
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash

from backend.database import db_config
from backend.security.passwords import password_policy_error


def requested_value(environment_name: str, prompt: str, default: str = "") -> str:
    configured = os.getenv(environment_name, "").strip()
    if configured:
        return configured
    suffix = f" [{default}]" if default else ""
    return input(f"{prompt}{suffix}: ").strip() or default


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    email = requested_value("BOOTSTRAP_ADMIN_EMAIL", "Administrator email")
    name = requested_value(
        "BOOTSTRAP_ADMIN_NAME", "Administrator name", "Project Administrator"
    )
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or getpass.getpass(
        "Administrator password (input is hidden): "
    )

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise SystemExit("A valid administrator email is required")
    policy_error = password_policy_error(password)
    if policy_error:
        raise SystemExit(policy_error)

    password_hash = generate_password_hash(password, method="scrypt")
    with psycopg.connect(**db_config(), row_factory=dict_row) as connection:
        row = connection.execute(
            "SELECT role_id FROM roles WHERE role_name = 'Admin'"
        ).fetchone()
        if not row:
            raise SystemExit("Admin role is missing; apply the canonical schema first")
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role_id, status)
            VALUES (%s, %s, %s, %s, 'active')
            ON CONFLICT (email) DO UPDATE SET
                name = EXCLUDED.name,
                password_hash = EXCLUDED.password_hash,
                role_id = EXCLUDED.role_id,
                status = 'active',
                session_version = users.session_version + 1
            """,
            (name, email, password_hash, row["role_id"]),
        )

    print(f"Administrator configured for {email}. The password was not stored in a file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
