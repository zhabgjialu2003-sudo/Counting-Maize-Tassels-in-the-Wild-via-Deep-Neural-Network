"""Human-friendly password policy for new and changed credentials."""

from __future__ import annotations


COMMON_PASSWORDS = {
    "123456",
    "12345678",
    "password",
    "password123",
    "qwerty123",
    "admin123",
}


def password_policy_error(password: str) -> str | None:
    if len(password) < 10:
        return "Password must be at least 10 characters"
    if len(password) > 128:
        return "Password must be 128 characters or fewer"
    if password.casefold() in COMMON_PASSWORDS:
        return "Choose a password that is harder to guess"
    if password.isspace():
        return "Password cannot contain only spaces"
    return None
