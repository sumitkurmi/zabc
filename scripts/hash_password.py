"""Utility script to generate bcrypt password hashes for admin authentication.

Usage:
    python scripts/hash_password.py <plain_password>
"""

import sys
import bcrypt


def hash_password(password: str) -> str:
    """Generates a secure bcrypt hash string for a given plain password."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        plain_pw = sys.argv[1]
    else:
        plain_pw = "admin123"
    hashed = hash_password(plain_pw)
    print(f"Plain:  {plain_pw}")
    print(f"Bcrypt Hash: {hashed}")
    print(f"Verified: {verify_password(plain_pw, hashed)}")
