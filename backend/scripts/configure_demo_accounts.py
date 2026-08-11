"""Explicitly provision the four local demonstration identities."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from backend.database import db_connection
from backend.demo_access import DEMO_ACCOUNTS, environment_flag
from backend.security.passwords import password_policy_error


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if not environment_flag("DEMO_ACCESS_ENABLED"):
        raise SystemExit("DEMO_ACCESS_ENABLED must be true before configuring demo accounts")

    password = os.getenv("DEMO_ACCOUNT_PASSWORD", "")
    policy_error = password_policy_error(password)
    if policy_error:
        raise SystemExit(f"DEMO_ACCOUNT_PASSWORD: {policy_error}")

    password_hash = generate_password_hash(password, method="scrypt")
    required_roles = {account["role"] for account in DEMO_ACCOUNTS}
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT role_id, role_name FROM roles WHERE role_name = ANY(%s)",
                (list(required_roles),),
            )
            role_ids = {row["role_name"]: row["role_id"] for row in cursor.fetchall()}
            missing_roles = sorted(required_roles - role_ids.keys())
            if missing_roles:
                raise RuntimeError("Missing required roles: " + ", ".join(missing_roles))

            for account in DEMO_ACCOUNTS:
                cursor.execute(
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
                    (
                        account["name"],
                        account["email"],
                        password_hash,
                        role_ids[account["role"]],
                    ),
                )

    print("Configured local demo accounts: " + ", ".join(a["email"] for a in DEMO_ACCOUNTS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
