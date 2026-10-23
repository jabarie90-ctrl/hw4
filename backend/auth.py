"""Password hashing for Campus Customs users.

Stored format: pbkdf2_sha256$<salt>$<hex digest>
Matches the seeded test user in data/campus_customs.db.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 120_000
HASH_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, salt: str | None = None) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 (120k iterations).

    On signup, omit salt so a fresh random salt is generated.
    On login, pass the salt from the stored hash string — never invent a new one.
    """
    if salt is None:
        salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{HASH_PREFIX}${salt}${digest.hex()}"


def parse_password_hash(stored: str) -> tuple[str, str, str]:
    """Split stored value into (prefix, salt, hex_digest)."""
    parts = stored.split("$")
    if len(parts) != 3 or parts[0] != HASH_PREFIX:
        raise ValueError("Unsupported password hash format")
    return parts[0], parts[1], parts[2]


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the typed password with the stored salt and compare constantly."""
    try:
        _, salt, expected = parse_password_hash(stored)
    except ValueError:
        return False
    candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, stored)
