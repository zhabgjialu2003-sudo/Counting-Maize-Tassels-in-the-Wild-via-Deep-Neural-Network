"""Local-only demo account metadata and exposure controls."""

from __future__ import annotations

import os
from ipaddress import ip_address
from typing import Final


DEMO_ACCOUNTS: Final[tuple[dict[str, str], ...]] = (
    {"name": "John Smith", "email": "john@farm.com", "role": "Farmer"},
    {"name": "Dr. Li Wei", "email": "liwei@research.org", "role": "Researcher"},
    {"name": "Maria Garcia", "email": "maria@agro.com", "role": "Agronomist"},
    {"name": "Admin User", "email": "admin@system.com", "role": "Admin"},
)

LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"localhost", "127.0.0.1", "::1"})


def environment_flag(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def normalized_hostname(host: str | None) -> str:
    value = (host or "").strip().casefold()
    if value.startswith("["):
        return value[1:].split("]", 1)[0]
    if value.count(":") == 1:
        return value.rsplit(":", 1)[0]
    return value


def demo_access_payload(host: str | None) -> dict:
    """Return credentials only for an explicitly enabled trusted local request."""
    if not environment_flag("DEMO_ACCESS_ENABLED"):
        return {"enabled": False}
    hostname = normalized_hostname(host)
    trusted_host = hostname in LOOPBACK_HOSTS
    if not trusted_host and environment_flag("DEMO_ACCESS_ALLOW_PRIVATE_NETWORK"):
        try:
            address = ip_address(hostname)
            trusted_host = address.is_private and not address.is_loopback
        except ValueError:
            trusted_host = False
    if not trusted_host:
        return {"enabled": False}
    password = os.getenv("DEMO_ACCOUNT_PASSWORD", "")
    if not password:
        return {"enabled": False}
    return {
        "enabled": True,
        "accounts": [dict(account) for account in DEMO_ACCOUNTS],
        "shared_password": password,
    }
